package native

import (
	"bytes"
	"testing"
)

func TestNativeOwnership(t *testing.T) {
	s, e := New(1)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	a, _ := s.Snapshot()
	f, _ := s.Render()
	b, _ := s.Snapshot()
	if !bytes.Equal(a, b) {
		t.Fatal("render mutated state")
	}
	if _, e = s.Command(map[string]any{"op": "input", "text": "Go direct"}); e != nil {
		t.Fatal(e)
	}
	g, _ := s.Render()
	if bytes.Equal(f.Bytes, g.Bytes) {
		t.Fatal("input missing")
	}
	if e = s.Restore(a); e != nil {
		t.Fatal(e)
	}
}
func TestRejectedAtomic(t *testing.T) {
	s, _ := New(2)
	defer s.Close()
	a, _ := s.Snapshot()
	if _, e := s.CommandRaw([]byte(`{"op":"resize","width":0}`)); e == nil {
		t.Fatal("accepted invalid")
	}
	b, _ := s.Snapshot()
	if !bytes.Equal(a, b) {
		t.Fatal("rejected mutation")
	}
}
