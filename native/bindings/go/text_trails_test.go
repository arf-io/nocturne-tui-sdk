package native

import "testing"

func TestTextTrailSample(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	_, e = s.CommandRaw([]byte(`{"op":"text","id":41,"text":"N","effect":"text/comet-stitch","phase":"hide","trailLength":8,"durationMs":1000,"variation":0,"staggerMs":0,"wind":2}`))
	if e != nil {
		t.Fatal(e)
	}
	if e = s.AdvanceTo(250000); e != nil {
		t.Fatal(e)
	}
	main, e := s.TextSample(41, 0)
	if e != nil {
		t.Fatal(e)
	}
	trail, e := s.TextTrailSample(41, 0, 7)
	if e != nil {
		t.Fatal(e)
	}
	dx := int64(trail[3]) - int64(main[3]) + 157286
	if trail[0] != main[2] || trail[1] != 78 || trail[2] != 8 || trail[5] <= 0 || dx < -100 || dx > 100 {
		t.Fatal(main, trail)
	}
	original := trail
	trail[0] = 0
	again, e := s.TextTrailSample(41, 0, 7)
	if e != nil || again != original {
		t.Fatal(again, e)
	}
	if _, e = s.TextTrailSample(41, 0, 8); e == nil {
		t.Fatal("invalid ordinal accepted")
	}
	if _, e = s.TextTrailSample(41, 1, 0); e == nil {
		t.Fatal("missing glyph accepted")
	}
	if e = s.AdvanceTo(2000000); e != nil {
		t.Fatal(e)
	}
	if _, e = s.TextTrailSample(41, 0, 0); e == nil {
		t.Fatal("settled trail accepted")
	}
	s.Close()
	if _, e = s.TextTrailSample(41, 0, 0); e == nil {
		t.Fatal("closed scene accepted")
	}
}
