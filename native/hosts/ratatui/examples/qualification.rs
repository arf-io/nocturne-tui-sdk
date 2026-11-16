//! Synthetic direct-native Ratatui qualification fixture, not a production gallery.
//! Run through ../qualify.py for input/render/exit and terminal-restoration assertions.
//! A missing Ratatui dependency blocks this whole target; helper tests are separate.
#![allow(non_snake_case)]
mod support;

use nocturne_native::{Frame as NativeFrame, NativeScene};
use nocturne_ratatui::SceneCells;
use ratatui::crossterm::{
    cursor::Show,
    event::{
        self, DisableBracketedPaste, DisableFocusChange, DisableMouseCapture, EnableBracketedPaste,
        EnableFocusChange, EnableMouseCapture, Event, KeyCode, KeyEventKind, KeyModifiers,
        MouseButton, MouseEventKind,
    },
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{backend::CrosstermBackend, Terminal};
use std::{
    env,
    fs::{File, OpenOptions},
    io::{self, IsTerminal, Write},
    panic::{catch_unwind, AssertUnwindSafe},
    path::PathBuf,
    time::{Duration, Instant},
};
use support::{clipboardCommand, frameHash, pasteCommand, jsonString, keyCommand, resizeCommand};

const MAX_TRACE_BYTES: usize = 8 * 1024 * 1024;
const MAX_LIFETIME: Duration = Duration::from_secs(20);

struct Trace {
    file: File,
    bytes: usize,
}
impl Trace {
    fn new(path: &PathBuf) -> io::Result<Self> {
        Ok(Self {
            file: OpenOptions::new().create_new(true).write(true).open(path)?,
            bytes: 0,
        })
    }

    fn record(
        &mut self,
        event: &str,
        scene: &mut NativeScene,
        frame: Option<&NativeFrame>,
        note: &str,
    ) -> io::Result<()> {
        let extra = frame
            .map(|f| {
                let mut hits = std::collections::BTreeMap::new();
                for (index, cell) in f.bytes.chunks_exact(16).enumerate() {
                    let owner = u32::from_le_bytes(cell[12..16].try_into().unwrap());
                    if owner & 0xff000000 == 0x10000000 {
                        hits.entry(owner & 0xffff).or_insert((index % f.width as usize, index / f.width as usize));
                    }
                }
                let nodes = hits.iter().map(|(owner, (x, y))| format!("\"{owner}\":[{x},{y}]"))
                    .collect::<Vec<_>>().join(",");
                format!(
                    ",\"width\":{},\"height\":{},\"frameFnv64\":\"{:016x}\",\"nodeHits\":{{{nodes}}}",
                    f.width,
                    f.height,
                    frameHash(&f.bytes)
                )
            })
            .unwrap_or_default();
        let line = format!(
            "{{\"event\":{},\"note\":{},\"info\":{}{extra}}}\n",
            jsonString(event),
            jsonString(note),
            scene.info()
        );
        if self.bytes + line.len() > MAX_TRACE_BYTES {
            return Err(io::Error::other("qualification trace bound exceeded"));
        }
        self.file.write_all(line.as_bytes())?;
        self.file.flush()?;
        self.bytes += line.len();
        Ok(())
    }
}

/// Own only this fixture's terminal session. Drop also runs during unwinding.
struct TerminalGuard {
    raw: bool,
    screen: bool,
    modes: bool,
}
impl TerminalGuard {
    fn enter(failSetup: bool, scene: &mut NativeScene, trace: &mut Trace) -> io::Result<Self> {
        let mut guard = Self {
            raw: false,
            screen: false,
            modes: false,
        };
        enable_raw_mode()?;
        guard.raw = true;
        if failSetup {
            // The PTY oracle must observe raw mode before it authorizes the failure.
            trace.record(
                "setup-raw",
                scene,
                None,
                "awaiting actual Ctrl-Q before injected setup failure",
            )?;
            let deadline = Instant::now() + Duration::from_secs(5);
            while Instant::now() < deadline {
                if event::poll(deadline.saturating_duration_since(Instant::now()))? {
                    match event::read()? {
                        Event::Key(key)
                            if key.kind != KeyEventKind::Release
                                && key.code == KeyCode::Char('q')
                                && key.modifiers.contains(KeyModifiers::CONTROL) =>
                        {
                            return Err(io::Error::other("intentional partial-startup failure"));
                        }
                        _ => {}
                    }
                }
            }
            return Err(io::Error::new(
                io::ErrorKind::TimedOut,
                "setup failure handshake not received",
            ));
        }
        // Mark attempts before writes so partially completed setup also cleans up.
        guard.screen = true;
        execute!(io::stdout(), EnterAlternateScreen)?;
        guard.modes = true;
        execute!(
            io::stdout(),
            EnableMouseCapture,
            EnableBracketedPaste,
            EnableFocusChange
        )?;
        Ok(guard)
    }

    fn restore(&mut self) -> io::Result<()> {
        let mut failure = None;
        // Independent attempts: an output error must not skip termios restoration.
        macro_rules! attempt {
            ($result:expr) => {
                if let Err(error) = $result {
                    if failure.is_none() {
                        failure = Some(error);
                    }
                }
            };
        }
        if self.modes {
            attempt!(execute!(io::stdout(), DisableMouseCapture));
            attempt!(execute!(io::stdout(), DisableBracketedPaste));
            attempt!(execute!(io::stdout(), DisableFocusChange));
            self.modes = false;
        }
        if self.screen {
            attempt!(execute!(io::stdout(), Show));
            attempt!(execute!(io::stdout(), LeaveAlternateScreen));
            attempt!(io::stdout().flush());
            self.screen = false;
        }
        if self.raw {
            attempt!(disable_raw_mode());
            self.raw = false;
        }
        failure.map_or(Ok(()), Err)
    }
}
impl Drop for TerminalGuard {
    fn drop(&mut self) {
        let _ = self.restore();
    }
}

fn apply(scene: &mut NativeScene, command: &str) -> io::Result<bool> {
    scene.command(command).map_err(io::Error::other)
}

fn configure(scene: &mut NativeScene, hold: bool) -> io::Result<()> {
    if let Some(path) = env::var_os("NOCTURNE_TEST_FIXTURE") {
        for command in std::fs::read_to_string(path)?.lines().filter(|line| !line.trim().is_empty()) {
            apply(scene, command)?;
        }
        apply(scene, &format!("{{\"op\":\"pause\",\"paused\":{hold}}}"))?;
        return Ok(());
    }
    for command in [
        r#"{"op":"environment","style":"solid","stars":0}"#,
        r#"{"op":"widget","id":90,"kind":"text","x":3,"y":3,"width":50,"height":1,"text":"RATATUI NATIVE PTY  █ ▀ ⣿","alpha":0}"#,
        r#"{"op":"widget","id":91,"kind":"button","x":4,"y":8,"width":22,"height":3,"text":"Native selection","border":"rounded","alpha":0.2}"#,
        r#"{"op":"state-register","id":1,"path":"/qualification/button","role":"control","target":{"family":"widget","id":91}}"#,
        r#"{"op":"prompt","mode":"grow","minRows":2,"maxRows":4}"#,
    ] {
        apply(scene, command)?;
    }
    apply(scene, &format!("{{\"op\":\"pause\",\"paused\":{hold}}}"))?;
    Ok(())
}

fn paint(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    scene: &mut NativeScene,
    trace: &mut Trace,
    ready: bool,
    viewport: &mut Option<(u16, u16)>,
) -> io::Result<()> {
    let size = terminal.size()?;
    if let Some(command) = resizeCommand(size.width, size.height, viewport) {
        apply(scene, &command)?;
    }
    let frame = scene.render().map_err(io::Error::other)?;
    // The adapter only sees the owned frame, never NativeScene or a simulation clock.
    terminal.draw(|area| area.render_widget(SceneCells { frame: &frame }, area.area()))?;
    trace.record(
        if ready { "ready" } else { "paint" },
        scene,
        Some(&frame),
        "native frame copied through Ratatui",
    )
}

fn mainLoop(
    terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    scene: &mut NativeScene,
    trace: &mut Trace,
    mut held: bool,
    failure: &str,
) -> io::Result<()> {
    let started = Instant::now();
    let mut lastWall = started;
    let mut targetUs = 0u64;
    let mut nextPaint = started;
    let mut first = true;
    let mut viewport = None;
    let mut dirty = true;
    let mut clipboard=String::new();
    loop {
        let now = Instant::now();
        if now.duration_since(started) >= MAX_LIFETIME {
            return Err(io::Error::new(
                io::ErrorKind::TimedOut,
                "qualification fixture lifetime expired",
            ));
        }
        if !held {
            targetUs += now.duration_since(lastWall).as_micros() as u64;
            // One bounded catch-up batch per turn. Input remains serviceable when behind.
            apply(
                scene,
                &format!("{{\"op\":\"time\",\"timeUs\":{targetUs},\"budget\":8}}"),
            )?;
        }
        lastWall = now;
        if dirty || now >= nextPaint {
            paint(terminal, scene, trace, first, &mut viewport)?;
            first = false;
            dirty = false;
            nextPaint = now + Duration::from_millis(33);
        }
        if !event::poll(Duration::from_millis(5))? {
            continue;
        }
        let mut command = None;
        match event::read()? {
            Event::Key(key) if key.kind != KeyEventKind::Release => {
                let ctrl = key.modifiers.contains(KeyModifiers::CONTROL);
                let shift = key.modifiers.contains(KeyModifiers::SHIFT);
                let alt = key.modifiers.contains(KeyModifiers::ALT);
                if ctrl && matches!(key.code, KeyCode::Char('q' | 'c')) {
                    if failure == "error" {
                        return Err(io::Error::other("intentional post-input failure"));
                    }
                    assert_ne!(
                        failure, "panic",
                        "intentional unwinding qualification panic"
                    );
                    return Ok(());
                }
                if (alt&&key.code==KeyCode::Char('w'))||(ctrl&&matches!(key.code,KeyCode::Char('w'|'y'))) {
                    let action=if alt{"copy"}else if key.code==KeyCode::Char('w'){"cut"}else{"paste"};
                    command=clipboardCommand(scene,&mut clipboard,action).map_err(io::Error::other)?;
                } else if ctrl && key.code == KeyCode::Char('p') {
                    held = !held;
                    lastWall = Instant::now();
                    command = Some(format!("{{\"op\":\"pause\",\"paused\":{held}}}"));
                } else if let KeyCode::Char(ch) = key.code {
                    command = Some(keyCommand(&ch.to_string(), ctrl, shift, alt));
                } else {
                    let name = match key.code {
                        KeyCode::Left => Some("ArrowLeft"),
                        KeyCode::Right => Some("ArrowRight"),
                        KeyCode::Up => Some("ArrowUp"),
                        KeyCode::Down => Some("ArrowDown"),
                        KeyCode::Home => Some("Home"),
                        KeyCode::End => Some("End"),
                        KeyCode::Backspace => Some("Backspace"),
                        KeyCode::Delete => Some("Delete"),
                        KeyCode::Enter => Some("Enter"),
                        KeyCode::Esc => Some("Escape"),
                        KeyCode::PageUp => Some("PageUp"),
                        KeyCode::PageDown => Some("PageDown"),
                        KeyCode::F(1) => Some("F1"),
                        KeyCode::F(6) => Some("F6"),
                        _ => None,
                    };
                    command = name.map(|name| keyCommand(name, ctrl, shift, alt));
                }
            }
            Event::Paste(text) => {
                command = Some(pasteCommand(&text));
            }
            Event::Resize(_, _) => {
                terminal.autoresize()?;
                dirty = true;
            }
            Event::FocusLost => {
                command = Some(r#"{"op":"pointer","phase":"cancel","x":-1,"y":-1}"#.to_string());
            }
            Event::Mouse(mouse) => {
                let x = mouse.column;
                let y = mouse.row;
                let shift = mouse.modifiers.contains(KeyModifiers::SHIFT);
                let alt = mouse.modifiers.contains(KeyModifiers::ALT);
                match mouse.kind {
                    MouseEventKind::ScrollUp | MouseEventKind::ScrollDown => {
                        let delta = if mouse.kind == MouseEventKind::ScrollUp {
                            1
                        } else {
                            -1
                        };
                        command = Some(format!("{{\"op\":\"wheel\",\"x\":{x},\"y\":{y},\"delta\":{delta},\"shift\":{shift}}}"));
                    }
                    MouseEventKind::Down(button)
                    | MouseEventKind::Up(button)
                    | MouseEventKind::Drag(button) => {
                        let phase = match mouse.kind {
                            MouseEventKind::Down(_) => "down",
                            MouseEventKind::Up(_) => "up",
                            _ => "move",
                        };
                        let button = match button {
                            MouseButton::Left => 0,
                            MouseButton::Middle => 1,
                            MouseButton::Right => 2,
                        };
                        command = Some(format!("{{\"op\":\"pointer\",\"phase\":\"{phase}\",\"x\":{x},\"y\":{y},\"button\":{button},\"shift\":{shift},\"alt\":{alt}}}"));
                    }
                    MouseEventKind::Moved => {
                        command = Some(format!("{{\"op\":\"pointer\",\"phase\":\"move\",\"x\":{x},\"y\":{y},\"shift\":{shift},\"alt\":{alt}}}"));
                    }
                    _ => {}
                }
            }
            _ => {}
        }
        if let Some(command) = command {
            apply(scene, &command)?;
            trace.record("input", scene, None, &command)?;
            dirty = true;
        }
    }
}

fn run(scene: &mut NativeScene, trace: &mut Trace, hold: bool, failure: &str) -> io::Result<()> {
    if !io::stdin().is_terminal() || !io::stdout().is_terminal() {
        return Err(io::Error::other(
            "qualification example requires terminal stdin and stdout",
        ));
    }
    configure(scene, hold)?;
    let mut guard = TerminalGuard::enter(failure == "setup", scene, trace)?;
    let mut terminal = Terminal::new(CrosstermBackend::new(io::stdout()))?;
    terminal.hide_cursor()?;
    let result = mainLoop(&mut terminal, scene, trace, hold, failure);
    let cleanup = guard.restore();
    result.and(cleanup)
}

fn entry() -> io::Result<i32> {
    let mut path = None;
    let mut held = false;
    let mut failure = String::from("none");
    let mut args = env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--trace" => {
                path = args.next().map(PathBuf::from);
            }
            "--hold" => {
                held = true;
            }
            "--failure" => {
                failure = args
                    .next()
                    .ok_or_else(|| io::Error::other("missing failure mode"))?;
            }
            "--help" => {
                println!(
                    "qualification --trace NEW_FILE [--hold] [--failure none|error|panic|setup]"
                );
                return Ok(0);
            }
            _ => {
                return Err(io::Error::other(format!("unknown argument: {arg}")));
            }
        }
    }
    if !matches!(failure.as_str(), "none" | "error" | "panic" | "setup") {
        return Err(io::Error::other("invalid failure mode"));
    }
    let mut trace =
        Trace::new(&path.ok_or_else(|| io::Error::other("--trace NEW_FILE is required"))?)?;
    let mut scene = NativeScene::new(2030).map_err(io::Error::other)?;
    let outcome = catch_unwind(AssertUnwindSafe(|| {
        run(&mut scene, &mut trace, held, &failure)
    }));
    // run's guard has already dropped before any exit record is written.
    let (code, note) = match outcome {
        Ok(Ok(())) => (0, "normal".to_string()),
        Ok(Err(error)) => (1, format!("error: {error}")),
        Err(payload) => {
            let message = payload
                .downcast_ref::<String>()
                .cloned()
                .or_else(|| {
                    payload
                        .downcast_ref::<&str>()
                        .map(|value| value.to_string())
                })
                .unwrap_or_else(|| "non-string panic".to_string());
            (101, format!("unwinding panic: {message}"))
        }
    };
    trace.record("exit", &mut scene, None, &note)?;
    // Qualification-only handshake: observe actual guard restoration before Darwin
    // revokes the terminal at session exit. Ordinary fixture calls do not wait.
    if let Some(path) = std::env::var_os("NOCTURNE_QUALIFICATION_EXIT_ACK") {
        let deadline = Instant::now() + Duration::from_secs(10);
        while !std::path::Path::new(&path).is_file() {
            if Instant::now() >= deadline {
                return Err(io::Error::other("qualification exit acknowledgement timeout"));
            }
            std::thread::sleep(Duration::from_millis(10));
        }
    }

    if code != 0 {
        eprintln!("{note}");
    }
    Ok(code)
}

fn main() {
    let code = match entry() {
        Ok(code) => code,
        Err(error) => {
            eprintln!("{error}");
            2
        }
    };
    std::process::exit(code);
}
