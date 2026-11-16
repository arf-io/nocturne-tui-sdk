package native

import (
	"strings"
	"testing"
)

func TestGeneratedWindowDocumentSource(t *testing.T) {
	s, err := New(2030)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	if _, err = s.CommandRaw([]byte(`{"op":"window","id":1,"title":"Window","text":"initial"}`)); err != nil {
		t.Fatal(err)
	}
	text := strings.Repeat("x", 4095) + "Z"
	if _, err = s.Command(map[string]any{"op": "window-content", "id": 1, "text": text}); err != nil {
		t.Fatal(err)
	}
	got, err := s.TextRunSource(2, 1)
	if err != nil || len([]rune(got)) != 4096 || got != text {
		t.Fatalf("4096-scalar source read: length=%d equal=%v err=%v", len([]rune(got)), got == text, err)
	}
	if _, err = s.Command(map[string]any{"op": "window-content", "id": 1, "text": ""}); err != nil {
		t.Fatal(err)
	}
	if got, err = s.TextRunSource(2, 1); err != nil || got != "" {
		t.Fatalf("empty source read: %q, %v", got, err)
	}
	if _, err = s.TextRunSource(2, 65535); err == nil {
		t.Fatal("missing source accepted")
	}
}
