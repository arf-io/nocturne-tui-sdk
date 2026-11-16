package native

import "testing"

func TestTextRunLayout(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	if _, e = s.CommandRaw([]byte(`{"op":"text","id":41,"text":"Aé中"}`)); e != nil {
		t.Fatal(e)
	}
	if hit, err := s.TextRunHit(1, 41, 3, 1, 1, 1); err != nil || hit != 4 {
		t.Fatal(hit, err)
	}
	if clipped, err := s.TextRunClip(1, 41, 8, 3, 0, 1, 1, 1); err != nil || len(clipped) != 1 || clipped[0] != [9]uint32{41, 3, 4, 2, 0, 2, 1, 1, 1} {
		t.Fatal(clipped, err)
	}
	text, e := s.TextRunSource(1, 41)
	if e != nil || text != "Aé中" {
		t.Fatal(text, e)
	}
	rows, e := s.TextRunLayout(1, 41, 3, 1)
	if e != nil || len(rows) != 3 || rows[2] != [7]uint32{41, 3, 4, 0, 1, 2, 1} {
		t.Fatal(rows, e)
	}
	rows[0][0] = 999
	again, e := s.TextRunLayout(1, 41, 8, 1)
	if e != nil || again[0][0] != 41 {
		t.Fatal(again, e)
	}
	if _, e = s.TextRunSource(1, 999); e == nil {
		t.Fatal("missing run accepted")
	}
	if _, e = s.TextRunLayout(1, 41, 0, 1); e == nil {
		t.Fatal("zero columns accepted")
	}
}

func TestTextClusterSample(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	if _, e = s.CommandRaw([]byte(`{"op":"text","id":41,"text":"AéZ"}`)); e != nil {
		t.Fatal(e)
	}
	old, e := s.TextClusterSample(41, 1)
	if e != nil || old[1] != 1 || old[2] != 3 {
		t.Fatal(old, e)
	}
	if _, e = s.CommandRaw([]byte(`{"op":"text","id":41,"text":"AèZ"}`)); e != nil {
		t.Fatal(e)
	}
	next, e := s.TextClusterSample(41, 1)
	if e != nil || next[0] == old[0] {
		t.Fatal(next, e)
	}
	if _, e = s.TextClusterSample(41, 3); e == nil {
		t.Fatal("missing cluster accepted")
	}
}
