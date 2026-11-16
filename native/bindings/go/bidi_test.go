package native

import "testing"

func TestBidiVisual(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	rows, e := s.BidiVisual("א12ב", 0)
	if e != nil || len(rows) != 4 || rows[0] != [4]uint32{3, 1, 1, 0x5d1} || rows[1] != [4]uint32{1, 3, 2, 49} {
		t.Fatal(rows, e)
	}
	rows[0][0] = 99
	again, e := s.BidiVisual("א12ב", 0)
	if e != nil || again[0][0] != 3 {
		t.Fatal(again, e)
	}
	if _, e = s.BidiVisual(string([]byte{255}), 0); e == nil {
		t.Fatal("malformed UTF8 accepted")
	}
	if _, e = s.BidiVisual("A", 3); e == nil {
		t.Fatal("invalid direction accepted")
	}
}

func TestBidiClusterLayout(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	rows, e := s.BidiLayout("א́ב", 8, 2, 1)
	if e != nil || len(rows) != 2 || rows[1] != [7]uint32{0, 2, 1, 0, 1, 1, 0x5d0} {
		t.Fatal(rows, e)
	}
	if _, e = s.BidiLayout("A", 0, 2, 1); e == nil {
		t.Fatal("zero columns accepted")
	}
}

func TestBidiCaretAffinity(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	hit, e := s.BidiHit("א́ב", 8, 0, 0, 2, 1)
	if e != nil || hit != 3 {
		t.Fatal(hit, e)
	}
	caret, e := s.BidiCaret("AאבB", 8, 1, 1, 2, 1)
	if e != nil || caret != [3]uint32{3, 0, 1} {
		t.Fatal(caret, e)
	}
	if _, e = s.BidiCaret("א́ב", 8, 1, 1, 2, 1); e == nil {
		t.Fatal("interior offset accepted")
	}
}
