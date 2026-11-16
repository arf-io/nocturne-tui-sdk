package native

import (
	"bytes"
	"encoding/json"
	"testing"
)

func TestWideUnboundValues(t *testing.T) {
	s, e := New(42)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, command := range []string{
		`{"op":"define","path":"/source","value":1000000000000,"readonly":true}`,
		`{"op":"define","path":"/out","value":0}`,
		`{"op":"set","path":"/out","expression":{"negate":{"path":"/source"}}}`,
	} {
		if _, e = s.CommandRaw([]byte(command)); e != nil {
			t.Fatal(e)
		}
	}
	raw, e := s.Info()
	if e != nil {
		t.Fatal(e)
	}
	var info struct {
		Values map[string]float64 `json:"values"`
	}
	if e = json.Unmarshal(raw, &info); e != nil || info.Values["/out"] != -1e12 {
		t.Fatal("wide expression", e)
	}
	for _, command := range []string{`{"op":"environment","background":0}`, `{"op":"set","path":"/out","value":16777215}`, `{"op":"bind","path":"/out","binding":{"family":"environment","id":0,"field":"background"}}`, `{"op":"bind","path":"/out","binding":null}`} {
		if _, e = s.CommandRaw([]byte(command)); e != nil {
			t.Fatal(e)
		}
	}
	before, e := s.Snapshot()
	if e != nil {
		t.Fatal("writer", e)
	}
	assertCurrentSnapshot(t, s, before)
	for _, command := range []string{`{"op":"set","path":"/out","value":1000000000001}`, `{"op":"set","path":"/source","value":0}`, `{"op":"bind","path":"/out","binding":{"family":"accessibility","id":0,"field":"screenReader"}}`} {
		if _, e = s.CommandRaw([]byte(command)); e == nil {
			t.Fatal("expected rejection")
		}
		after, e := s.Snapshot()
		if e != nil || !bytes.Equal(before, after) {
			t.Fatal("rollback", e)
		}
	}
	if e = s.Restore(before); e != nil {
		t.Fatal(e)
	}
	after, e := s.Snapshot()
	if e != nil || !bytes.Equal(before, after) {
		t.Fatal("restore", e)
	}
}
