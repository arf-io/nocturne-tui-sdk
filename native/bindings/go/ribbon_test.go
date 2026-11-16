package native

import (
	"bytes"
	"encoding/json"
	"testing"
)

func TestRibbonMatchesAuthoredGeometry(t *testing.T) {
	a, e := New(17)
	if e != nil {
		t.Fatal(e)
	}
	defer a.Close()
	b, e := New(17)
	if e != nil {
		t.Fatal(e)
	}
	defer b.Close()
	if _, e = a.CommandRaw([]byte(`{"op":"ribbon","points":[[0,0,0],[4,0,0]],"width":2}`)); e != nil {
		t.Fatal(e)
	}
	if _, e = b.CommandRaw([]byte(`{"op":"mesh","triangles":[{"a":[0,0,-1],"b":[0,0,1],"c":[4,0,-1]},{"a":[0,0,1],"b":[4,0,1],"c":[4,0,-1]}]}`)); e != nil {
		t.Fatal(e)
	}
	x, e := a.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	y, e := b.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(x, y) {
		t.Fatal("ribbon differs from independent mesh")
	}
}

func TestPathTravel(t *testing.T) {
	s, e := New(17)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	r, e := s.PathSample([][3]float64{{0, 0, 0}, {3, 0, 0}, {3, 4, 0}}, 5, false, 0)
	if e != nil || r != [8]float64{3, 2, 0, 0, 1, 0, 7, 5} {
		t.Fatal(r, e)
	}
}

func TestRetainedPathTravel(t *testing.T) {
	s, e := New(17)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	if _, e = s.CommandRaw([]byte(`{"op":"path-travel","id":1,"target":{"family":"camera","id":0},"points":[[0,0,0],[4,0,0]],"speed":2}`)); e != nil {
		t.Fatal(e)
	}
	if e = s.AdvanceTo(1000000); e != nil {
		t.Fatal(e)
	}
	info, e := s.Info()
	if e != nil {
		t.Fatal(e)
	}
	var decoded struct {
		Camera struct {
			Position [3]float64 `json:"position"`
		} `json:"camera"`
	}
	if e = json.Unmarshal(info, &decoded); e != nil {
		t.Fatal(e)
	}
	if decoded.Camera.Position != [3]float64{2, 0, 0} {
		t.Fatal(decoded.Camera.Position)
	}
}
