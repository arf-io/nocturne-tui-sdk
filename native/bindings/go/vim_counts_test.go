package native

import (
	"encoding/json"
	"testing"
)

func TestCountedVimDeleteUndo(t *testing.T) {
	s, e := New(17)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, c := range []string{`{"op":"prompt","mode":"vim-inline"}`, `{"op":"draft","text":"abcdef","caret":0,"emitWeather":false}`, `{"op":"key","key":"Escape"}`, `{"op":"key","key":"3"}`, `{"op":"key","key":"x"}`} {
		if _, e = s.CommandRaw([]byte(c)); e != nil {
			t.Fatal(e)
		}
	}
	info, e := s.Info()
	if e != nil {
		t.Fatal(e)
	}
	var v struct{ Prompt struct{ Text string } }
	if e = json.Unmarshal(info, &v); e != nil {
		t.Fatal(e)
	}
	if v.Prompt.Text != "def" {
		t.Fatal(v.Prompt.Text)
	}
	if _, e = s.CommandRaw([]byte(`{"op":"key","key":"P"}`)); e != nil {
		t.Fatal(e)
	}
	info, e = s.Info()
	if e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(info, &v); e != nil {
		t.Fatal(e)
	}
	if v.Prompt.Text != "abcdef" {
		t.Fatal(v.Prompt.Text)
	}

	for _, key := range []string{"z", "r"} {
		if _, e = s.Command(map[string]any{"op": "key", "key": key, "ctrl": true}); e != nil {
			t.Fatal(e)
		}
	}
	info, e = s.Info()
	if e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(info, &v); e != nil {
		t.Fatal(e)
	}
	if v.Prompt.Text != "abcdef" {
		t.Fatal(v.Prompt.Text)
	}

}
func TestNamedVimRegister(t *testing.T) {
	s, e := New(17)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, c := range []any{map[string]any{"op": "prompt", "mode": "vim-inline"}, map[string]any{"op": "draft", "text": "saved", "caret": 0, "emitWeather": false}, map[string]any{"op": "key", "key": "Escape"}} {
		if _, e = s.Command(c); e != nil {
			t.Fatal(e)
		}
	}
	for _, k := range []string{"\"", "a", "y", "w"} {
		if _, e = s.Command(map[string]any{"op": "key", "key": k}); e != nil {
			t.Fatal(e)
		}
	}
	if _, e = s.Command(map[string]any{"op": "draft", "text": "Z", "caret": 0, "emitWeather": false}); e != nil {
		t.Fatal(e)
	}
	for _, k := range []string{"Escape", "\"", "a", "P"} {
		if _, e = s.Command(map[string]any{"op": "key", "key": k}); e != nil {
			t.Fatal(e)
		}
	}
	info, e := s.Info()
	if e != nil {
		t.Fatal(e)
	}
	var v struct{ Prompt struct{ Text string } }
	if e = json.Unmarshal(info, &v); e != nil {
		t.Fatal(e)
	}
	if v.Prompt.Text != "savedZ" {
		t.Fatal(v.Prompt.Text)
	}
}
