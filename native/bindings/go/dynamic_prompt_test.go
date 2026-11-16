package native

import (
	"bytes"
	"strings"
	"testing"
	"unicode/utf8"
)

func TestDynamicPromptGrowthAndRestore(t *testing.T) {
	s, err := New(2030)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	command := func(v any) {
		t.Helper()
		if _, e := s.Command(v); e != nil {
			t.Fatal(e)
		}
	}
	command(map[string]any{"op": "prompt", "presentation": "framed"})
	text := ""
	for _, n := range []int{35001, 35003, 70007} {
		part := strings.Repeat("🌧", n)
		command(map[string]any{"op": "input", "text": part})
		text += part
		got, e := s.TextRunSource(0, 0)
		if e != nil || got != text {
			t.Fatalf("source count %d: %v", utf8.RuneCountInString(got), e)
		}
	}
	count := utf8.RuneCountInString(text)
	command(map[string]any{"op": "select", "anchor": 0, "caret": count})
	selected, e := s.SelectedText()
	if e != nil || selected != text {
		t.Fatalf("selection: %v", e)
	}
	clusters, e := s.TextRunClusters(0, 0)
	if e != nil || len(clusters) != count {
		t.Fatalf("clusters %d: %v", len(clusters), e)
	}
	layout, e := s.TextRunLayout(0, 0, 80, 1)
	if e != nil || len(layout) != count {
		t.Fatalf("layout %d: %v", len(layout), e)
	}
	if _, e = s.Render(); e != nil {
		t.Fatal(e)
	}
	saved, e := s.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	restored, e := New(99)
	if e != nil {
		t.Fatal(e)
	}
	defer restored.Close()
	if e = restored.Restore(saved); e != nil {
		t.Fatal(e)
	}
	got, e := restored.TextRunSource(0, 0)
	if e != nil || got != text {
		t.Fatalf("restore: %v", e)
	}
	before, e := s.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	if _, e = s.Command(map[string]any{"op": "select", "anchor": 0, "caret": -1}); e == nil {
		t.Fatal("invalid edit accepted")
	}
	after, e := s.Snapshot()
	if e != nil || !bytes.Equal(before, after) {
		t.Fatalf("invalid edit mutated state: %v", e)
	}
}

func TestDynamicPromptLargeUTF8Command(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	if _, e = s.Command(map[string]any{"op": "prompt", "presentation": "framed"}); e != nil {
		t.Fatal(e)
	}
	text := strings.Repeat("🌧", 270001)
	if _, e = s.Command(map[string]any{"op": "draft", "text": text, "emitWeather": false}); e != nil {
		t.Fatal(e)
	}
	got, e := s.TextRunSource(0, 0)
	if e != nil || got != text {
		t.Fatalf("large command: %v", e)
	}
}
