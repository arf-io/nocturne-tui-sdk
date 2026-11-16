package main

import (
	"bytes"
	tea "github.com/charmbracelet/bubbletea"
	"strings"
	"testing"
)

func TestUnicodeDocumentLargeSource(t *testing.T) {
	m := testModel(t)
	m.unicodeDocument = true
	m.documentWidth, m.documentHeight = 79, 20
	text := "ABC" + strings.Repeat("Aא́👩‍🔧ב\tZ\n", 7001)
	m.apply(map[string]any{"op": "draft", "text": text, "caret": 0, "emitWeather": false})
	before, _ := m.scene.Snapshot()
	m.paint()
	after, _ := m.scene.Snapshot()
	if m.err != nil || !bytes.Equal(before, after) {
		t.Fatal("large paint", m.err)
	}
	m.documentMouse(tea.MouseMsg{X: 1, Y: 1, Button: tea.MouseButtonLeft, Action: tea.MouseActionPress})
	m.apply(map[string]any{"op": "draft", "text": "X" + text, "emitWeather": false})
	m.documentMouse(tea.MouseMsg{X: 4, Y: 1, Button: tea.MouseButtonLeft, Action: tea.MouseActionMotion})
	if m.err != nil || m.documentDrag == nil || *m.documentDrag != 2 {
		t.Fatal("large retained anchor", m.err, m.documentDrag)
	}
	m.documentMouse(tea.MouseMsg{X: 4, Y: 1, Button: tea.MouseButtonLeft, Action: tea.MouseActionRelease})
	source, e := m.scene.TextRunSource(0, 0)
	if e != nil || source != "X"+text {
		t.Fatal("source changed", e)
	}
	if !m.documentMove("pgdown", true) {
		t.Fatal("page navigation ignored")
	}
	m.paint()
	if m.err != nil {
		t.Fatal(m.err)
	}
}

func TestUnicodeDocumentWheelHeaderIgnored(t *testing.T) {
	m := testModel(t)
	m.unicodeDocument = true
	m.documentWidth, m.documentHeight = 20, 4
	m.apply(map[string]any{"op": "draft", "text": strings.Repeat("line\n", 20), "caret": 0, "emitWeather": false})
	m.paint()
	before, _ := m.scene.Snapshot()
	scroll := m.documentScroll
	m = testUpdate(t, m, tea.MouseMsg{Y: 0, Button: tea.MouseButtonWheelDown})
	after, _ := m.scene.Snapshot()
	if scroll != m.documentScroll || !bytes.Equal(before, after) {
		t.Fatal("header wheel changed document")
	}
}
