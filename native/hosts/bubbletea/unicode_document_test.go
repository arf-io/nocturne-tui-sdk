package main

import (
	"bytes"
	tea "github.com/charmbracelet/bubbletea"
	"strings"
	"testing"
)

func TestUnicodeDocumentClustersAndPurity(t *testing.T) {
	m := testModel(t)
	m.unicodeDocument = true
	m.documentWidth, m.documentHeight = 20, 8
	m.apply(map[string]any{"op": "paste", "text": "א́👩‍🔧ב"})
	before, _ := m.scene.Snapshot()
	m.paint()
	if m.err != nil {
		t.Fatal(m.err)
	}
	view := m.View()
	if !strings.Contains(view, "ב👩‍🔧א́") {
		t.Fatalf("whole clusters in visual order missing: %q", view)
	}
	after, _ := m.scene.Snapshot()
	if !bytes.Equal(before, after) {
		t.Fatal("document presentation mutated scene")
	}
}

func TestUnicodeDocumentPointerUsesSourceMapping(t *testing.T) {
	m := testModel(t)
	m.unicodeDocument = true
	m.documentWidth, m.documentHeight = 20, 8
	m.apply(map[string]any{"op": "paste", "text": "אב"})
	m = testUpdate(t, m, tea.MouseMsg{X: 0, Y: 1, Button: tea.MouseButtonLeft, Action: tea.MouseActionPress})
	m = testUpdate(t, m, tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("X")})
	source, err := m.scene.TextRunSource(0, 0)
	if err != nil || source != "אבX" {
		t.Fatalf("pointer mapping: %q %v", source, err)
	}
}

func TestUnicodeDocumentScrollAndOwnerFallback(t *testing.T) {
	m := testModel(t)
	m.unicodeDocument = true
	m.documentWidth, m.documentHeight = 20, 4
	m.apply(map[string]any{"op": "paste", "text": strings.Repeat("line\n", 20)})
	m.apply(map[string]any{"op": "select", "anchor": 0, "caret": 0, "unit": "grapheme"})
	m.paint()
	before, _ := m.scene.Snapshot()
	m = testUpdate(t, m, tea.MouseMsg{Y: 1, Button: tea.MouseButtonWheelDown})
	after, _ := m.scene.Snapshot()
	if m.documentScroll != 3 || !bytes.Equal(before, after) {
		t.Fatal("wheel must scroll the host viewport without changing native state")
	}
	m.apply(map[string]any{"op": "prompt", "active": false})
	m.paint()
	if strings.Contains(m.View(), "NOCTURNE Unicode document") {
		t.Fatal("document captured another input owner")
	}
}

func TestUnicodeDocumentNavigationAndDrag(t *testing.T) {
	m := testModel(t)
	m.unicodeDocument = true
	m.documentWidth, m.documentHeight = 20, 4
	m.apply(map[string]any{"op": "paste", "text": "ABCDE\nX\nABCDE"})
	m.apply(map[string]any{"op": "select", "anchor": 4, "caret": 4, "unit": "grapheme"})
	m.paint()
	m = testUpdate(t, m, tea.KeyMsg{Type: tea.KeyDown})
	if p := testInfo(t, m)["prompt"].(map[string]any); p["caret"] != float64(7) {
		t.Fatal(p)
	}
	m = testUpdate(t, m, tea.KeyMsg{Type: tea.KeyDown})
	if p := testInfo(t, m)["prompt"].(map[string]any); p["caret"] != float64(12) {
		t.Fatal(p)
	}
	m = testUpdate(t, m, tea.MouseMsg{X: 0, Y: 1, Button: tea.MouseButtonLeft, Action: tea.MouseActionPress})
	m = testUpdate(t, m, tea.MouseMsg{X: 3, Y: 1, Button: tea.MouseButtonLeft, Action: tea.MouseActionMotion})
	m = testUpdate(t, m, tea.MouseMsg{X: 3, Y: 1, Button: tea.MouseButtonLeft, Action: tea.MouseActionRelease})
	selected, err := m.scene.SelectedText()
	if err != nil || selected != "ABC" {
		t.Fatalf("drag %q %v", selected, err)
	}
}

func TestUnicodeDocumentCaretScrollKeepsManualScroll(t *testing.T) {
	m := testModel(t)
	m.unicodeDocument = true
	m.documentWidth, m.documentHeight = 20, 4
	m.apply(map[string]any{"op": "paste", "text": strings.Repeat("line\n", 20)})
	m.paint()
	if m.documentScroll < 18 {
		t.Fatalf("caret hidden at scroll %d", m.documentScroll)
	}
	m = testUpdate(t, m, tea.MouseMsg{Y: 1, Button: tea.MouseButtonWheelUp})
	scroll := m.documentScroll
	m.paint()
	if m.documentScroll != scroll {
		t.Fatal("repaint undid manual scroll")
	}
	m = testUpdate(t, m, tea.KeyMsg{Type: tea.KeyRunes, Runes: []rune("X")})
	if m.documentScroll <= scroll {
		t.Fatal("edited caret did not return into view")
	}
}

func TestDragTracksRetainedNativeClusterAcrossSourceEdits(t *testing.T){
 m:=testModel(t);m.unicodeDocument=true;m.documentWidth,m.documentHeight=20,8
 m.apply(map[string]any{"op":"draft","text":"ABC","emitWeather":false});m.documentMouse(tea.MouseMsg{X:1,Y:1,Button:tea.MouseButtonLeft,Action:tea.MouseActionPress})
 m.apply(map[string]any{"op":"draft","text":"XABC","emitWeather":false});m.documentMouse(tea.MouseMsg{X:4,Y:1,Button:tea.MouseButtonLeft,Action:tea.MouseActionMotion})
 text,e:=m.scene.SelectedText();if m.err!=nil||e!=nil||text!="BC"||m.documentDrag==nil||*m.documentDrag!=2{t.Fatal(text,m.documentDrag,m.err,e)}
 m.documentMouse(tea.MouseMsg{X:4,Y:0,Button:tea.MouseButtonLeft,Action:tea.MouseActionRelease});if m.documentDrag!=nil{t.Fatal("release above document retained drag")}
}
func TestRetiredDragClusterCancelsWithoutSourceMutation(t *testing.T){
 m:=testModel(t);m.unicodeDocument=true;m.documentWidth,m.documentHeight=20,8
 m.apply(map[string]any{"op":"draft","text":"ABC","emitWeather":false});m.documentMouse(tea.MouseMsg{X:1,Y:1,Button:tea.MouseButtonLeft,Action:tea.MouseActionPress})
 m.apply(map[string]any{"op":"draft","text":"AXC","emitWeather":false});before,_:=m.scene.Snapshot();m.documentMouse(tea.MouseMsg{X:3,Y:1,Button:tea.MouseButtonLeft,Action:tea.MouseActionMotion});after,_:=m.scene.Snapshot()
 if m.err!=nil||m.documentDrag!=nil||!bytes.Equal(before,after){t.Fatal("retired anchor selected unrelated source",m.err)}
}
