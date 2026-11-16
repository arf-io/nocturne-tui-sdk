package native

import (
	"reflect"
	"strings"
	"testing"
)

func TestDocumentCapacity(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, text := range []string{"", "AאבB", "א́👩‍🔧ב\tA\nב"} {
		for d := uint32(0); d < 3; d++ {
			a, e := s.DocumentLayout(text, 7, d, 1)
			if e != nil {
				t.Fatal(e)
			}
			b, e := s.BidiLayout(text, 7, d, 1)
			if e != nil || !reflect.DeepEqual(a, b) {
				t.Fatal("layout", e)
			}
			bounds, e := s.DocumentBoundaries(text)
			if e != nil {
				t.Fatal(e)
			}
			for _, off := range bounds {
				for af := uint32(0); af < 2; af++ {
					a, e := s.DocumentCaret(text, 7, off, af, d, 1)
					b, f := s.BidiCaret(text, 7, off, af, d, 1)
					if e != nil || f != nil || a != b {
						t.Fatal("caret", a, b, e, f)
					}
				}
			}
			for _, xy := range [][2]uint32{{0, 0}, {3, 0}, {0, 3}} {
				a, e := s.DocumentHit(text, 7, xy[0], xy[1], d, 1)
				b, f := s.BidiHit(text, 7, xy[0], xy[1], d, 1)
				if e != nil || f != nil || a != b {
					t.Fatal("hit", a, b, e, f)
				}
			}
		}
	}
	for _, text := range []string{strings.Repeat("אב", 2501), strings.Repeat("Aא́👩‍🔧ב\tZ\n", 7001)} {
		rows, e := s.DocumentLayout(text, 79, 2, 1)
		if e != nil || len(rows) <= 2048 {
			t.Fatal(len(rows), e)
		}
	}
	if _, e := s.DocumentLayout(string([]byte{0xff}), 8, 2, 1); e == nil {
		t.Fatal("invalid UTF accepted")
	}
}
