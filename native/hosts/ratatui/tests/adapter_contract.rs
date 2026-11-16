//! Dependency-backed adapter contracts. No replacement Ratatui or native implementation.
#![allow(non_snake_case)]
use nocturne_native::{Frame, NativeScene};
use nocturne_ratatui::SceneCells;
use ratatui::{
    backend::TestBackend, buffer::Buffer, layout::Rect, style::Color, widgets::Widget, Terminal,
};

fn makeFrame(width: u32, height: u32, glyphs: &[u32]) -> Frame {
    let bytes = glyphs
        .iter()
        .enumerate()
        .flat_map(|(index, &glyph)| {
            [
                glyph,
                0x102030 + index as u32,
                0x405060 + index as u32,
                0x70000000 + index as u32,
            ]
            .into_iter()
            .flat_map(u32::to_le_bytes)
        })
        .collect();
    Frame {
        width,
        height,
        bytes,
    }
}

#[test]
fn glyphForegroundBackgroundAndSemanticBytesStayOwned() {
    let native = makeFrame(1, 1, &[0x28ff]);
    let before = native.clone();
    let area = Rect::new(3, 4, 1, 1);
    let mut buffer = Buffer::empty(area);
    SceneCells { frame: &native }.render(area, &mut buffer);
    assert_eq!(buffer[(3, 4)].symbol(), "⣿");
    assert_eq!(buffer[(3, 4)].fg, Color::Rgb(0x10, 0x20, 0x30));
    assert_eq!(buffer[(3, 4)].bg, Color::Rgb(0x40, 0x50, 0x60));
    assert_eq!(native, before);
}

#[test]
fn cropUsesSourceStrideAndDoesNotTouchNeighbours() {
    let native = makeFrame(3, 2, &[65, 66, 67, 68, 69, 70]);
    let mut buffer = Buffer::empty(Rect::new(0, 0, 9, 8));
    for cell in &mut buffer.content {
        cell.set_symbol(".");
    }
    SceneCells { frame: &native }.render(Rect::new(3, 4, 2, 2), &mut buffer);
    for y in 0..8 {
        for x in 0..9 {
            let expected = match (x, y) {
                (3, 4) => "A",
                (4, 4) => "B",
                (3, 5) => "D",
                (4, 5) => "E",
                _ => ".",
            };
            assert_eq!(buffer[(x, y)].symbol(), expected, "at {x},{y}");
        }
    }
}

#[test]
fn supportedCellHalfAndBrailleGlyphsKeepTheirFamily() {
    let native = makeFrame(5, 1, &[0x2588, 0x2580, 0x2584, 0x2801, 0x28ff]);
    let area = Rect::new(0, 0, 5, 1);
    let mut buffer = Buffer::empty(area);
    SceneCells { frame: &native }.render(area, &mut buffer);
    for (x, expected) in ["█", "▀", "▄", "⠁", "⣿"].iter().enumerate() {
        assert_eq!(buffer[(x as u16, 0)].symbol(), *expected);
    }
}

#[test]
fn unsupportedScalarsHaveExplicitSingleCellReplacement() {
    let native = makeFrame(6, 1, &[0x754c, 0x301, 0x1b, 0xd800, 0x110000, 0x1f600]);
    let before = native.clone();
    let area = Rect::new(0, 0, 6, 1);
    let mut buffer = Buffer::empty(area);
    SceneCells { frame: &native }.render(area, &mut buffer);
    for x in 0..6 {
        assert_eq!(buffer[(x, 0)].symbol(), "�");
    }
    assert_eq!(native, before); // The authoritative Unicode is not replaced.
}

#[test]
fn zeroAreaDoesNotModifyTheBuffer() {
    let native = makeFrame(1, 1, &[65]);
    let mut buffer = Buffer::empty(Rect::new(0, 0, 3, 3));
    let before = buffer.clone();
    SceneCells { frame: &native }.render(Rect::new(1, 1, 0, 0), &mut buffer);
    assert_eq!(buffer, before);
}

#[test]
fn shortFrameNeverReadsAnIncompleteCell() {
    let mut native = makeFrame(2, 1, &[65, 66]);
    native.bytes.truncate(31);
    let area = Rect::new(0, 0, 2, 1);
    let mut buffer = Buffer::empty(area);
    SceneCells { frame: &native }.render(area, &mut buffer);
    assert_eq!(buffer[(0, 0)].symbol(), "A");
    assert_eq!(buffer[(1, 0)].symbol(), " ");
}

#[test]
fn actualTerminalTestBackendReceivesTheNativeFrame() -> Result<(), Box<dyn std::error::Error>> {
    let native = makeFrame(3, 1, &[65, 0x2580, 0x28ff]);
    let mut terminal = Terminal::new(TestBackend::new(5, 2))?;
    terminal.draw(|frame| frame.render_widget(SceneCells { frame: &native }, frame.area()))?;
    let buffer = terminal.backend().buffer();
    assert_eq!(buffer[(0, 0)].symbol(), "A");
    assert_eq!(buffer[(1, 0)].symbol(), "▀");
    assert_eq!(buffer[(2, 0)].symbol(), "⣿");
    assert_eq!(buffer[(3, 0)].symbol(), " ");
    Ok(())
}

#[test]
fn currentCoreStateAndCopiedFramesSurviveAdapterRendering() -> Result<(), String> {
    let mut scene = NativeScene::new(2030)?;
    scene.command(r#"{"op":"resize","width":40,"height":12}"#)?;
    scene.command(r#"{"op":"pause","paused":true}"#)?;
    scene.command(r#"{"op":"input","text":"owned é text"}"#)?;
    let snapshot = scene.snapshot()?;
    let native = scene.render()?;
    let before = native.clone();
    let area = Rect::new(0, 0, 40, 12);
    let mut buffer = Buffer::empty(area);
    SceneCells { frame: &native }.render(area, &mut buffer);
    assert_eq!(scene.snapshot()?, snapshot);
    assert_eq!(native, before);
    scene.command(r#"{"op":"input","text":" later"}"#)?;
    scene.render()?;
    assert_eq!(native, before);
    assert!(scene.info().contains("owned é text later"));
    Ok(())
}

#[test]
fn partiallyOverlappingBufferClipsWithoutChangingSourceOrigin() {
    let native = makeFrame(3, 2, &[65, 66, 67, 68, 69, 70]);
    let before = native.clone();
    let mut buffer = Buffer::empty(Rect::new(4, 5, 3, 2));
    for cell in &mut buffer.content {
        cell.set_symbol(".");
    }
    SceneCells { frame: &native }.render(Rect::new(3, 4, 3, 2), &mut buffer);
    assert_eq!(buffer[(4, 5)].symbol(), "E");
    assert_eq!(buffer[(5, 5)].symbol(), "F");
    assert_eq!(buffer[(6, 5)].symbol(), ".");
    assert_eq!(buffer[(4, 6)].symbol(), ".");
    assert_eq!(native, before);
}

#[test]
fn disjointBufferIsAnUntouchedNoOp() {
    let native = makeFrame(2, 1, &[65, 66]);
    let mut buffer = Buffer::empty(Rect::new(20, 20, 2, 2));
    let before = buffer.clone();
    SceneCells { frame: &native }.render(Rect::new(0, 0, 2, 1), &mut buffer);
    assert_eq!(buffer, before);
}

#[test]
fn malformedLargeStrideDoesNotWrapOrPanic() {
    let native = makeFrame(1 << 28, 2, &[65]);
    let before = native.clone();
    let area = Rect::new(0, 0, 1, 2);
    let mut buffer = Buffer::empty(area);
    SceneCells { frame: &native }.render(area, &mut buffer);
    assert_eq!(buffer[(0, 0)].symbol(), "A");
    assert_eq!(buffer[(0, 1)].symbol(), " ");
    assert_eq!(native, before);
}

#[test]
fn statusAreaScalarCellsSourceSnapshotAndRenderedAction() -> Result<(), String> {
    const MESSAGE: &str = "Aé界e\u{301}Z";
    const LABEL: &str = "Review é";
    const HIT_ID: u32 = 0x63000000 | (37 << 2); // slot zero, not public action ID 17
    let mut scene = NativeScene::new(18)?;
    for command in [
        r#"{"op":"resize","width":48,"height":16}"#,
        r#"{"op":"environment","stars":0}"#,
        r#"{"op":"prompt","active":false}"#,
        r#"{"op":"pause","paused":true}"#,
        r#"{"op":"area","id":1,"x":4,"y":3,"width":30,"height":6,"border":"none","padding":0,"layout":"direct","alpha":1}"#,
        r#"{"op":"status","id":37,"area":1,"text":"Aé界e\u0301Z","x":0,"y":0,"mode":"pop","durationMs":0,"actions":[{"id":17,"label":"Review é","event":"/status/scalar/review","value":7}]}"#,
    ] {
        scene.command(command)?;
    }
    // The native binding deliberately has no JSON dependency. Match complete
    // text/label fields in the sole message record, not a display string.
    fn messages(info: &str) -> &str {
        info.split_once("\"messages\":[")
            .unwrap()
            .1
            .split_once("],\"intents\":[")
            .unwrap()
            .0
    }
    fn number(record: &str, key: &str) -> f64 {
        record
            .split_once(&format!("\"{key}\":"))
            .unwrap()
            .1
            .split([',', '}'])
            .next()
            .unwrap()
            .parse()
            .unwrap()
    }
    let info = scene.info();
    let source = messages(&info).to_owned();
    assert!(
        source.starts_with(&format!(
            "{{\"id\":37,\"text\":\"{MESSAGE}\",\"state\":\"active\""
        )),
        "{source}"
    );
    assert!(
        source.contains(&format!(
            "\"actions\":[{{\"id\":17,\"label\":\"{LABEL}\",\"event\":\"/status/scalar/review\","
        )),
        "{source}"
    );
    assert_eq!(number(&source, "value"), 7.0);
    let snapshot = scene.snapshot()?;
    let mut original: Option<Frame> = None;
    for phase in ["original", "restored"] {
        assert_eq!(scene.snapshot()?, snapshot, "{phase}: snapshot recovery");
        assert_eq!(messages(&scene.info()), source, "{phase}: source recovery");
        let native = scene.render()?; // Real C output, never makeFrame().
        assert_eq!(
            (native.width, native.height, native.bytes.len()),
            (48, 16, 48 * 16 * 16)
        );
        let before = original.get_or_insert_with(|| native.clone());
        assert_eq!(&native, &*before);
        let word = |x: usize, y: usize, field: usize| {
            let offset = (y * 48 + x) * 16 + field * 4;
            u32::from_le_bytes(native.bytes[offset..offset + 4].try_into().unwrap())
        };
        for (i, glyph) in [0x41, 0xe9, 0x754c, 0x65, 0x301, 0x5a]
            .into_iter()
            .enumerate()
        {
            assert_eq!(word(4 + i, 3, 0), glyph, "{phase}: native scalar cell {i}");
            assert_eq!(word(4 + i, 3, 3), 0, "message cell is not an action");
        }
        for (i, glyph) in LABEL.chars().enumerate() {
            assert_eq!(word(5 + i, 5, 0), glyph as u32, "native action label {i}");
        }
        let hits: Vec<_> = (0..16)
            .flat_map(|y| (0..48).map(move |x| (x, y)))
            .filter(|&(x, y)| word(x, y, 3) == HIT_ID)
            .collect();
        let expected: Vec<_> = (4..7).flat_map(|y| (4..16).map(move |x| (x, y))).collect();
        assert_eq!(hits, expected, "{phase}: semantic action cells shifted");
        let mut terminal = Terminal::new(TestBackend::new(48, 16)).map_err(|e| e.to_string())?;
        for _ in 0..2 {
            terminal
                .draw(|frame| frame.render_widget(SceneCells { frame: &native }, frame.area()))
                .map_err(|e| e.to_string())?;
            let buffer = terminal.backend().buffer();
            for (i, symbol) in ["A", "é", "�", "e", "�", "Z"].into_iter().enumerate() {
                assert_eq!(
                    buffer[(4 + i as u16, 3)].symbol(),
                    symbol,
                    "{phase}: display cell {i}"
                );
            }
            for x in [3, 10] {
                assert_eq!(
                    buffer[(x as u16, 3)].symbol(),
                    char::from_u32(word(x, 3, 0)).unwrap().to_string(),
                    "neighbor {x} shifted"
                );
            }
            for (i, glyph) in LABEL.chars().enumerate() {
                assert_eq!(
                    buffer[(5 + i as u16, 5)].symbol(),
                    glyph.to_string(),
                    "action label shifted"
                );
            }
            assert_eq!(
                scene.snapshot()?,
                snapshot,
                "TestBackend rendering mutated snapshot"
            );
            assert_eq!(messages(&scene.info()), source);
            assert_eq!(
                &native,
                original.as_ref().unwrap(),
                "adapter mutated owned frame"
            );
        }
        assert_eq!(scene.render()?, native, "repeat C render changed frame");
        assert_eq!(scene.snapshot()?, snapshot);
        // Select a semantic hit from the actual C label cells, then deliver input
        // to the same native scene. This presentation-only adapter does not own input.
        let &(x, y) = hits
            .iter()
            .find(|&&(x, y)| word(x, y, 0) == 'é' as u32)
            .unwrap();
        for pointer_phase in ["down", "up"] {
            scene.command(&format!(
                r#"{{"op":"pointer","phase":"{pointer_phase}","x":{x},"y":{y}}}"#
            ))?;
        }
        let activated = scene.info();
        let intent = activated
            .split_once("\"intents\":[")
            .unwrap()
            .1
            .split_once("],\"registeredStates\":[")
            .unwrap()
            .0;
        assert!(
            intent.starts_with("{\"id\":1,") && !intent.contains("},{"),
            "{intent}"
        );
        assert!(
            intent.contains(r#""event":"/status/scalar/review","#),
            "{intent}"
        );
        for (key, expected) in [
            ("messageId", 37.0),
            ("actionId", 17.0),
            ("messageSequence", 1.0),
            ("value", 7.0),
            ("atUs", 0.0),
        ] {
            assert_eq!(number(intent, key), expected, "intent {key}");
        }
        assert!(messages(&activated).contains(&format!("\"text\":\"{MESSAGE}\"")));
        assert!(messages(&activated).contains(&format!("\"label\":\"{LABEL}\"")));
        assert_eq!(&native, original.as_ref().unwrap());
        scene.command(r#"{"op":"clear","scope":"status"}"#)?;
        assert_eq!(
            messages(&scene.info()),
            "",
            "restore precondition: message was not removed"
        );
        assert_ne!(scene.snapshot()?, snapshot);
        scene.restore(&snapshot)?;
        assert_eq!(scene.snapshot()?, snapshot);
        let recovered = scene.info();
        assert_eq!(messages(&recovered), source);
        assert!(recovered.contains(r#""intents":[]"#));
    }
    Ok(())
}
