// Native Bubble Tea host. View only returns an already rendered owned frame.
// Host-specific qualification and platform limits are recorded in README.md.
package main

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/mattn/go-runewidth"
	native "nocturne/native"
	"os"
	"strings"
	"time"
)

type documentAnchor struct{identity,generation uint32;end bool;source string}
type documentSignature struct {
	source               string
	caret, width, height int
}
type tickMsg time.Time
type model struct {
 shortcuts *shortcutProfile
 reservedShortcuts []string
 shortcutToolbar bool
 terminalHeight int
	scene                                         *native.Scene
	view                                          string
	err                                           error
	clock                                         uint64
	last                                          time.Time
	paused                                        bool
	clipboard                                     string
	unicodeDocument                               bool
	documentWidth, documentHeight, documentScroll int
	documentDrag                                  *uint32
 documentIdentity *documentAnchor
	documentPreferred                             *int
	documentLast                                  *documentSignature
}

func (m *model) clipboardAction(action string) {
	raw, err := m.scene.InfoComplete()
	if err != nil {
		m.err = err
		return
	}
	var info struct {
		InputOwner string `json:"inputOwner"`
		Prompt     struct {
			Text   string `json:"text"`
			Anchor int    `json:"anchor"`
			Caret  int    `json:"caret"`
		} `json:"prompt"`
	}
	if err = json.Unmarshal(raw, &info); err != nil {
		m.err = err
		return
	}
	if info.InputOwner != "prompt" {
		return
	}
	if action == "paste" {
		if m.clipboard != "" {
			m.apply(map[string]any{"op": "paste", "text": m.clipboard})
		}
		return
	}
	p := info.Prompt
	if action == "cut" && (p.Anchor < 0 || p.Anchor == p.Caret) {
		return
	}
	text := p.Text
	if p.Anchor >= 0 {
		text, err = m.scene.SelectedText()
		if err != nil {
			m.err = err
			return
		}
	}
	m.clipboard = text
	if action == "cut" {
		m.apply(map[string]any{"op": "key", "key": "Delete"})
	}
}

func tick() tea.Cmd           { return tea.Tick(time.Second/60, func(t time.Time) tea.Msg { return tickMsg(t) }) }
func (m model) Init() tea.Cmd { return tick() }
func (m *model) apply(v any) {
 if command,ok:=v.(map[string]any);ok&&command["op"]=="reset"{m.cancelDocumentDrag()}
	if m.err == nil {
		_, m.err = m.scene.Command(v)
	}
}
func (m *model) paint() {
 m.ensureShortcuts();if m.err!=nil{return}
	if m.unicodeDocument && m.paintDocument() {
		return
	}
	f, e := m.scene.Render()
	if e != nil {
		m.err = e
		return
	}
	var b strings.Builder
	for y := uint32(0); y < f.Height; y++ {
		for x := uint32(0); x < f.Width; x++ {
			i := int((y*f.Width + x) * 16)
			if i+16 > len(f.Bytes) {
				m.err = fmt.Errorf("short native frame")
				return
			}
			glyph := rune(binary.LittleEndian.Uint32(f.Bytes[i:]))
			fg := binary.LittleEndian.Uint32(f.Bytes[i+4:])
			bg := binary.LittleEndian.Uint32(f.Bytes[i+8:])
			if glyph < 32 || runewidth.RuneWidth(glyph) != 1 {
				glyph = '\uFFFD'
			}
			fmt.Fprintf(&b, "\x1b[38;2;%d;%d;%d;48;2;%d;%d;%dm%c", fg>>16&255, fg>>8&255, fg&255, bg>>16&255, bg>>8&255, bg&255, glyph)
		}
		b.WriteString("\x1b[0m")
		if y+1 < f.Height {
			b.WriteByte('\n')
		}
	}
	m.view = b.String()
}
func (m model) Update(message tea.Msg) (tea.Model, tea.Cmd) {
 m.ensureShortcuts();if m.err!=nil{return m,tea.Quit}
	var next tea.Cmd
	switch msg := message.(type) {
	case tickMsg:
		now := time.Time(msg)
		if !m.paused {
			elapsed := now.Sub(m.last).Microseconds()
			if elapsed > 0 {
				m.clock += uint64(elapsed)
			}
			m.apply(map[string]any{"op": "time", "timeUs": m.clock, "budget": 240})
		}
		m.last = now
		next = tick()
	case tea.WindowSizeMsg:
		m.terminalHeight=msg.Height
        height:=max(1,msg.Height);if m.shortcutToolbar&&height>1{height--}
		m.documentWidth, m.documentHeight = max(1, msg.Width), height
		m.apply(map[string]any{"op": "resize", "width": max(1, msg.Width), "height": height})
	case tea.KeyMsg:
		if msg.Paste {
			// A pasted control remains data and reaches native validation; it
			// cannot become an application shortcut or a Vim command.
			m.apply(map[string]any{"op": "paste", "text": string(msg.Runes)})
			break
		}
		key := msg.String()
		if m.unicodeDocument && m.documentMove(strings.TrimPrefix(key, "shift+"), strings.HasPrefix(key, "shift+")) {
			break
		}
        if key=="ctrl+c"{return m,tea.Quit}
        action:=m.shortcuts.bindings[key]
        if action==1{return m,tea.Quit}
        if action==2{m.paused=!m.paused;m.apply(map[string]any{"op":"pause","paused":m.paused});m.last=time.Now();break}
        if action>=3&&action<=5{m.clipboardAction(map[uint32]string{3:"copy",4:"cut",5:"paste"}[action]);break}
        if action==6||action==7{k:="F1";if action==7{k="F6"};m.apply(map[string]any{"op":"key","key":k});break}
        if m.shortcuts.managed[key]{break}
		named := map[string]string{"up": "ArrowUp", "down": "ArrowDown", "left": "ArrowLeft", "right": "ArrowRight", "home": "Home", "end": "End", "backspace": "Backspace", "delete": "Delete", "esc": "Escape", "pgup": "PageUp", "pgdown": "PageDown"}
		if strings.HasPrefix(key, "shift+") {
			if k, ok := named[strings.TrimPrefix(key, "shift+")]; ok {
				m.apply(map[string]any{"op": "key", "key": k, "shift": true})
				break
			}
		}
		if k, ok := named[key]; ok {
			m.apply(map[string]any{"op": "key", "key": k})
		} else if key == "ctrl+a" || key == "ctrl+e" || key == "ctrl+z" {
			m.apply(map[string]any{"op": "key", "key": key[5:], "ctrl": true})
		} else if key == "enter" {
			m.apply(map[string]any{"op": "key", "key": "Enter"})
		} else if len(msg.Runes) > 0 {
			// Bubble Tea may group ordinary runes from one read. Dispatch each
			// through native key ownership in order, including mode changes.
			for _, char := range msg.Runes {
				m.apply(map[string]any{"op": "key", "key": string(char), "alt": msg.Alt})
			}
		}
	case tea.BlurMsg:
		m.cancelDocumentDrag()
		m.apply(map[string]any{"op": "pointer", "phase": "cancel", "x": 0, "y": 0})
	case tea.MouseMsg:
		if m.unicodeDocument && m.documentMouse(msg) {
			break
		}
		if msg.Button == tea.MouseButtonWheelUp || msg.Button == tea.MouseButtonWheelDown {
			d := 1
			if msg.Button == tea.MouseButtonWheelDown {
				d = -1
			}
			m.apply(map[string]any{"op": "wheel", "x": msg.X, "y": msg.Y, "delta": d, "shift": msg.Shift})
			break
		}
		phase := "down"
		if msg.Action == tea.MouseActionMotion {
			phase = "move"
		}
		if msg.Action == tea.MouseActionRelease {
			phase = "up"
		}
		button := 0
		if msg.Button == tea.MouseButtonMiddle {
			button = 1
		}
		if msg.Button == tea.MouseButtonRight {
			button = 2
		}
		m.apply(map[string]any{"op": "pointer", "phase": phase, "x": msg.X, "y": msg.Y, "button": button, "shift": msg.Shift, "alt": msg.Alt})
	}
	m.paint()
	if m.err != nil {
		return m, tea.Quit
	}
	return m, next
}
func (m model) View() string {
 if !m.shortcutToolbar||m.shortcuts==nil||m.terminalHeight==1{return m.view}
 hints:=m.shortcuts.hints;if m.documentWidth>0&&len(hints)>m.documentWidth{hints=hints[:m.documentWidth]}
 return m.view+"\n\x1b[0m"+hints
}

// runModel is the shared application/test lifecycle, not a new SDK interface.
func runModel(m tea.Model) (tea.Model, error) {
	result, err := tea.NewProgram(m, tea.WithAltScreen(), tea.WithMouseAllMotion(), tea.WithReportFocus()).Run()
	// Pinned Bubble Tea 1.3.4 restores the terminal on a recovered event-loop
	// panic but returns (nil, nil). Absence of a final model is never success.
	if result == nil && err == nil {
		err = fmt.Errorf("Bubble Tea exited without a final model after recovery")
	}
	return result, err
}

func main() {
	s, err := native.New(2030)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer s.Close()
	m := model{scene: s, last: time.Now(), documentWidth: 80, documentHeight: 24,shortcutToolbar:true}
	infoPath := ""
	for _, arg := range os.Args[1:] {
        if strings.HasPrefix(arg,"--reserve-shortcut="){m.reservedShortcuts=append(m.reservedShortcuts,strings.TrimPrefix(arg,"--reserve-shortcut="))}
		if arg == "--paused" {
			m.paused = true
			m.apply(map[string]any{"op": "pause", "paused": true})
		}
		if strings.HasPrefix(arg, "--document-text=") {
			m.apply(map[string]any{"op": "paste", "text": strings.TrimPrefix(arg, "--document-text=")})
		}
		if strings.HasPrefix(arg, "--info-on-exit=") {
			infoPath = strings.TrimPrefix(arg, "--info-on-exit=")
		}
		if arg == "--unicode-document" {
			m.unicodeDocument = true
		}
	}
	m.apply(map[string]any{"op": "emitter", "id": 1, "effect": "weather/autumn-drift", "count": 240, "runningTimeMs": 20000})
	m.paint()
	result, err := runModel(m)
	if err == nil {
		if final, ok := result.(model); ok {
			err = final.err
			if err == nil && infoPath != "" {
				var raw []byte
				raw, err = final.scene.InfoComplete()
				if err == nil {
					err = os.WriteFile(infoPath, raw, 0600)
				}
			}
		}
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
