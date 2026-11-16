package native

import (
	"bytes"
	"encoding/json"
	"testing"
)

func TestNumericExpressions(t *testing.T) {
	s, e := New(42)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, command := range []string{`{"op":"define","path":"/scale","value":2}`, `{"op":"define","path":"/out","value":0}`, `{"op":"set","path":"/out","expression":{"add":[{"multiply":[{"path":"/scale"},4]},3]}}`} {
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
	if e = json.Unmarshal(raw, &info); e != nil || info.Values["/out"] != 11 {
		t.Fatal("native expression", e)
	}
	before, e := s.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	if _, e = s.CommandRaw([]byte(`{"op":"set","path":"/out","expression":{"divide":[1,0]}}`)); e == nil {
		t.Fatal("accepted division by zero")
	}
	after, e := s.Snapshot()
	if e != nil || !bytes.Equal(before, after) {
		t.Fatal("rejection mutated source", e)
	}
}
