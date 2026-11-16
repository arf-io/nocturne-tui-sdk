package native

import "testing"

func TestGraphemeHit(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, c := range []struct {
		text             string
		cols, x, y, want uint32
	}{{"é中", 8, 1, 0, 2}, {"👩‍🔧A", 8, 1, 0, 3}, {"A\r\n", 8, 0, 1, 3}, {"", 1, 0, 0, 0}} {
		got, e := s.GraphemeHit(c.text, c.cols, c.x, c.y, 1)
		if e != nil || got != c.want {
			t.Fatalf("%+v: %v %v", c, got, e)
		}
	}
	if _, e := s.GraphemeHit("A", 0, 0, 0, 1); e == nil {
		t.Fatal("zero columns accepted")
	}
	if _, e := s.GraphemeHit(string([]byte{255}), 1, 0, 0, 1); e == nil {
		t.Fatal("invalid UTF-8 accepted")
	}
}
