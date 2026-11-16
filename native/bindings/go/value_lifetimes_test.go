package native

import (
	"bytes"
	"encoding/json"
	"testing"
)

func TestValueLifetimes(t *testing.T) {
	s, e := New(42)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, command := range []string{`{"op":"define","path":"/source","value":0}`, `{"op":"define","path":"/target","value":0}`, `{"op":"trigger","id":1,"source":"/source","target":"/target"}`} {
		if _, e = s.CommandRaw([]byte(command)); e != nil {
			t.Fatal(e)
		}
	}
	before, e := s.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	if _, e = s.CommandRaw([]byte(`{"op":"remove-value","path":"/source"}`)); e == nil {
		t.Fatal("removed referenced source")
	}
	after, e := s.Snapshot()
	if e != nil || !bytes.Equal(before, after) {
		t.Fatal("rejection mutated state", e)
	}
	for _, command := range []string{`{"op":"remove-trigger","id":1}`, `{"op":"remove-value","path":"/source"}`, `{"op":"define","path":"/replacement","value":9}`} {
		if _, e = s.CommandRaw([]byte(command)); e != nil {
			t.Fatal(e)
		}
	}
	raw, e := s.Info()
	if e != nil {
		t.Fatal(e)
	}
	var info struct {
		Values   map[string]float64 `json:"values"`
		Triggers []any              `json:"triggers"`
	}
	if e = json.Unmarshal(raw, &info); e != nil {
		t.Fatal(e)
	}
	if _, exists := info.Values["/source"]; exists || len(info.Triggers) != 0 || info.Values["/replacement"] != 9 {
		t.Fatal("lifetime/slot reuse mismatch")
	}
}
