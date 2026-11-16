package main

import (
	"encoding/json"
	tea "github.com/charmbracelet/bubbletea"
	native "nocturne/native"
	"testing"
)

func TestClipboardSelectionKeys(t *testing.T) {
	s, e := native.New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	m := model{scene: s}
	m.apply(map[string]any{"op": "draft", "text": "Aé日本Z", "caret": 1, "emitWeather": false})
	m.apply(map[string]any{"op": "select", "anchor": 1, "caret": 5})
	for _, key := range []tea.KeyMsg{{Type: tea.KeyRunes, Runes: []rune{'w'}, Alt: true}, {Type: tea.KeyCtrlW}, {Type: tea.KeyCtrlY}} {
		next, _ := m.Update(key)
		m = next.(model)
	}
	if m.err != nil {
		t.Fatal(m.err)
	}
	if m.clipboard != "é日本" {
		t.Fatal(m.clipboard)
	}
	raw, _ := s.Info()
	var info struct {
		Prompt struct {
			Text string `json:"text"`
		} `json:"prompt"`
	}
	json.Unmarshal(raw, &info)
	if info.Prompt.Text != "Aé日本Z" {
		t.Fatal(info.Prompt.Text)
	}
	m.apply(map[string]any{"op": "key", "key": "F1"})
	before, _ := s.Snapshot()
	next, _ := m.Update(tea.KeyMsg{Type: tea.KeyCtrlW})
	m = next.(model)
	after, _ := s.Snapshot()
	if string(before) != string(after) {
		t.Fatal("modal cut mutated scene")
	}
}
func TestShiftArrowSelection(t *testing.T) {
	s, e := native.New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	m := model{scene: s}
	m.apply(map[string]any{"op": "draft", "text": "AB", "caret": 0, "emitWeather": false})
	next, _ := m.Update(tea.KeyMsg{Type: tea.KeyShiftRight})
	m = next.(model)
	if m.err != nil {
		t.Fatal(m.err)
	}
	raw, _ := s.Info()
	var info struct {
		Prompt struct {
			Anchor int `json:"anchor"`
			Caret  int `json:"caret"`
		} `json:"prompt"`
	}
	json.Unmarshal(raw, &info)
	if info.Prompt.Anchor != 0 || info.Prompt.Caret != 1 {
		t.Fatal(string(raw))
	}
}
