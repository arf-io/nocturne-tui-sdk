package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	tea "github.com/charmbracelet/bubbletea"
	native "nocturne/native"
	"reflect"
	"regexp"
	"strings"
	"testing"
	"time"
)

func testModel(t *testing.T) model {
	t.Helper()
	s, e := native.New(2030)
	if e != nil {
		t.Fatal(e)
	}
	t.Cleanup(s.Close)
	m := model{scene: s, last: time.Now(), paused: true}
	for _, cmd := range []any{
		map[string]any{"op": "resize", "width": 80, "height": 24},
		map[string]any{"op": "pause", "paused": true},
		map[string]any{"op": "widget", "id": 1, "kind": "button", "text": "Inspect", "x": 8, "y": 9, "width": 18, "height": 3},
		map[string]any{"op": "state-register", "id": 1, "path": "/test/button", "role": "button", "target": map[string]any{"family": "widget", "id": 1}},
	} {
		m.apply(cmd)
	}
	if m.err != nil {
		t.Fatal(m.err)
	}
	m.paint()
	return m
}
func testInfo(t *testing.T, m model) map[string]any {
	t.Helper()
	b, e := m.scene.Info()
	if e != nil {
		t.Fatal(e)
	}
	var v map[string]any
	if e = json.Unmarshal(b, &v); e != nil {
		t.Fatal(e)
	}
	return v
}
func testUpdate(t *testing.T, m model, msg tea.Msg) model {
	t.Helper()
	v, _ := m.Update(msg)
	m = v.(model)
	if m.err != nil {
		t.Fatal(m.err)
	}
	return m
}
func TestHeldEditAndPaste(t *testing.T) {
	m := testModel(t)
	m = testUpdate(t, m, tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("abc")})
	m = testUpdate(t, m, tea.KeyMsg{Type: tea.KeyLeft})
	m = testUpdate(t, m, tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("é")})
	m = testUpdate(t, m, tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune(" \"\\"), Paste: true})
	info := testInfo(t, m)
	p := info["prompt"].(map[string]any)
	if p["text"] != "abé \"\\c" {
		t.Fatalf("paste/edit: %v", p)
	}
	if info["clock"].(map[string]any)["timeUs"] != float64(0) {
		t.Fatal("held input advanced time")
	}
}
func TestViewAndPaintArePure(t *testing.T) {
	m := testModel(t)
	a, e := m.scene.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	original := m.View()
	m.paint()
	if original != m.View() {
		t.Fatal("paint changed held view")
	}
	b, e := m.scene.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(a, b) {
		t.Fatal("paint/View mutated scene")
	}
}
func TestFocusLossClearsNativePointer(t *testing.T) {
	m := testModel(t)
	m = testUpdate(t, m, tea.MouseMsg{X: 9, Y: 10, Action: tea.MouseActionMotion, Button: tea.MouseButtonNone})
	m = testUpdate(t, m, tea.MouseMsg{X: 9, Y: 10, Action: tea.MouseActionPress, Button: tea.MouseButtonLeft})
	before := testInfo(t, m)["registeredStates"].([]any)[0].(map[string]any)["states"].(map[string]any)
	if before["hover"] != true || before["pressed"] != true {
		t.Fatal("precondition", before)
	}
	m = testUpdate(t, m, tea.BlurMsg{})
	after := testInfo(t, m)["registeredStates"].([]any)[0].(map[string]any)["states"].(map[string]any)
	if after["hover"] != false || after["pressed"] != false {
		t.Fatal("focus loss retained capture", after)
	}
}
func TestResizeAndNativeError(t *testing.T) {
	m := testModel(t)
	m = testUpdate(t, m, tea.WindowSizeMsg{Width: 100, Height: 30})
	f, e := m.scene.Render()
	if e != nil || f.Width != 100 || f.Height != 30 {
		t.Fatal("resize", e)
	}
	m.apply(map[string]any{"op": "invalid-qualification-command"})
	if m.err == nil {
		t.Fatal("native rejection lost")
	}
	out, cmd := m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("x")})
	if out.(model).err == nil || cmd == nil {
		t.Fatal("error must quit")
	}
}
func TestPastedControlRejectedByNativeContract(t *testing.T) {
	m := testModel(t)
	m = testUpdate(t, m, tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("retained")})
	before, e := m.scene.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	out, cmd := m.Update(tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune{17}, Paste: true})
	m = out.(model)
	if m.err == nil || cmd == nil {
		t.Fatal("unsupported C0 paste must report native error, not Ctrl-Q success")
	}
	after, e := m.scene.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(before, after) {
		t.Fatal("rejected paste changed source document")
	}
}

// Starts at the actual C notification, not a fabricated adapter frame.
func TestStatusAreaScalarCellsSourceSnapshotAndRenderedAction(t *testing.T) {
	const message = "Aé界e\u0301Z"
	const label = "Review é"
	const event = "/status/scalar/review"
	const hitID uint32 = 0x63000000 | (37 << 2) // slot zero; public action ID is 17
	s, err := native.New(18)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(s.Close)
	m := model{scene: s, last: time.Now(), paused: true}
	for _, cmd := range []any{
		map[string]any{"op": "resize", "width": 48, "height": 16},
		map[string]any{"op": "environment", "stars": 0},
		map[string]any{"op": "prompt", "active": false},
		map[string]any{"op": "pause", "paused": true},
		map[string]any{"op": "area", "id": 1, "x": 4, "y": 3, "width": 30, "height": 6, "border": "none", "padding": 0, "layout": "direct", "alpha": 1},
		map[string]any{"op": "status", "id": 37, "area": 1, "text": message, "x": 0, "y": 0, "mode": "pop", "durationMs": 0,
			"actions": []any{map[string]any{"id": 17, "label": label, "event": event, "value": 7}}},
	} {
		m.apply(cmd)
	}
	if m.err != nil {
		t.Fatal(m.err)
	}
	snapshot := func() []byte {
		t.Helper()
		b, e := s.Snapshot()
		if e != nil {
			t.Fatal(e)
		}
		return b
	}
	record := func() map[string]any {
		t.Helper()
		records := testInfo(t, m)["messages"].([]any)
		if len(records) != 1 {
			t.Fatalf("messages: %v", records)
		}
		return records[0].(map[string]any)
	}
	source := record()
	if source["id"] != float64(37) || source["text"] != message || source["actions"].([]any)[0].(map[string]any)["label"] != label {
		t.Fatal("source changed", source)
	}
	saved := snapshot()
	var original []byte
	for _, phase := range []string{"original", "restored"} {
		if !bytes.Equal(snapshot(), saved) || !reflect.DeepEqual(record(), source) {
			t.Fatalf("%s: restore/source mismatch", phase)
		}
		f, e := s.Render()
		if e != nil {
			t.Fatal(e)
		}
		if f.Width != 48 || f.Height != 16 || len(f.Bytes) != 48*16*16 {
			t.Fatal("native frame bounds")
		}
		if original == nil {
			original = append([]byte(nil), f.Bytes...)
		}
		if !bytes.Equal(f.Bytes, original) {
			t.Fatalf("%s: native frame recovery", phase)
		}
		word := func(x, y, field int) uint32 { return binary.LittleEndian.Uint32(f.Bytes[(y*48+x)*16+field*4:]) }
		for i, g := range []uint32{0x41, 0xe9, 0x754c, 0x65, 0x301, 0x5a} {
			if word(4+i, 3, 0) != g || word(4+i, 3, 3) != 0 {
				t.Fatalf("%s: native scalar cell %d: U+%04X", phase, i, word(4+i, 3, 0))
			}
		}
		var hits [][2]int
		var expected [][2]int
		for y := 0; y < 16; y++ {
			for x := 0; x < 48; x++ {
				if word(x, y, 3) == hitID {
					hits = append(hits, [2]int{x, y})
				}
			}
		}
		for y := 4; y < 7; y++ {
			for x := 4; x < 16; x++ {
				expected = append(expected, [2]int{x, y})
			}
		}
		if !reflect.DeepEqual(hits, expected) {
			t.Fatalf("%s: semantic action cells: %v", phase, hits)
		}
		for i, g := range []rune(label) {
			if word(5+i, 5, 0) != uint32(g) {
				t.Fatalf("action source glyph %d", i)
			}
		}
		m.paint() // The real Bubble Tea model renders another actual C frame.
		if m.err != nil {
			t.Fatal(m.err)
		}
		view := m.View()
		rows := strings.Split(regexp.MustCompile(`\x1b\[[0-9;]*m`).ReplaceAllString(view, ""), "\n")
		if len(rows) != 16 {
			t.Fatalf("rendered rows: %d", len(rows))
		}
		for y, row := range rows {
			if len([]rune(row)) != 48 {
				t.Fatalf("%s: row %d shifted: %q", phase, y, row)
			}
		}
		row := []rune(rows[3])
		for i, g := range []rune{'A', 'é', '\uFFFD', 'e', '\uFFFD', 'Z'} {
			if row[4+i] != g {
				t.Fatalf("%s: display cell %d: got U+%04X want U+%04X", phase, i, row[4+i], g)
			}
		}
		for _, x := range []int{3, 10} {
			if row[x] != rune(word(x, 3, 0)) {
				t.Fatalf("neighbor %d shifted", x)
			}
		}
		if string([]rune(rows[5])[5:13]) != label {
			t.Fatalf("action label shifted: %q", rows[5])
		}
		m.paint()
		if m.err != nil || m.View() != view || !bytes.Equal(snapshot(), saved) || !reflect.DeepEqual(record(), source) {
			t.Fatalf("%s: paint/View mutated source: %v", phase, m.err)
		}
		if !bytes.Equal(f.Bytes, original) {
			t.Fatal("adapter mutated copied native frame")
		}
		x, y := -1, -1
		for _, p := range hits {
			if word(p[0], p[1], 0) == uint32('é') {
				x, y = p[0], p[1]
				break
			}
		}
		if x < 0 {
			t.Fatal("C action-label hit missing")
		}
		m = testUpdate(t, m, tea.MouseMsg{X: x, Y: y, Action: tea.MouseActionPress, Button: tea.MouseButtonLeft})
		m = testUpdate(t, m, tea.MouseMsg{X: x, Y: y, Action: tea.MouseActionRelease, Button: tea.MouseButtonLeft})
		intents := testInfo(t, m)["intents"].([]any)
		if len(intents) != 1 {
			t.Fatalf("%s: intents %v", phase, intents)
		}
		intent := intents[0].(map[string]any)
		if intent["messageId"] != float64(37) || intent["actionId"] != float64(17) || intent["event"] != event || intent["value"] != float64(7) {
			t.Fatal("semantic action mapping", intent)
		}
		if record()["text"] != message || record()["actions"].([]any)[0].(map[string]any)["label"] != label {
			t.Fatal("activation changed source text")
		}
		m.apply(map[string]any{"op": "clear", "scope": "status"})
		if m.err != nil {
			t.Fatal(m.err)
		}
		if len(testInfo(t, m)["messages"].([]any)) != 0 || bytes.Equal(snapshot(), saved) {
			t.Fatal("restore precondition: source was not removed")
		}
		if e = s.Restore(saved); e != nil {
			t.Fatal(e)
		}
		if !bytes.Equal(snapshot(), saved) || !reflect.DeepEqual(record(), source) || len(testInfo(t, m)["intents"].([]any)) != 0 {
			t.Fatal("snapshot did not recover exact source/action")
		}
	}
}

func TestBracketedPastePreservesModalInputOwnership(t *testing.T) {
 m := testModel(t)
 m.apply(map[string]any{"op":"key", "key":"F1"})
 before, err := m.scene.Snapshot(); if err != nil {t.Fatal(err)}
 m = testUpdate(t, m, tea.KeyMsg{Type:tea.KeyRunes, Runes:[]rune("X"), Paste:true})
 after, err := m.scene.Snapshot(); if err != nil {t.Fatal(err)}
 if !bytes.Equal(before,after) {t.Fatal("paste edited prompt owned by modal")}
}
