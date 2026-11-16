package native

import (
	"math"
	"testing"
)

func TestWaveSample(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	v, e := s.WaveSample([][5]float64{{2, 3, 4, 5, .2}}, .1, .2, .3)
	if e != nil || math.Abs(v[0]-2*math.Cos(-.2)) > 1e-11 {
		t.Fatal(v, e)
	}
	if _, e = s.WaveSample([][5]float64{{math.NaN(), 0, 0, 0, 0}}, 0, 0, 0); e == nil {
		t.Fatal("nonfinite accepted")
	}
}
func TestRetainedSurfaceWave(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, c := range []any{map[string]any{"op": "surface", "id": 1}, map[string]any{"op": "surface-waves", "surfaceId": 1, "waves": [][5]float64{{2, 0, 0, 0, 0}}}} {
		if _, e = s.Command(c); e != nil {
			t.Fatal(e)
		}
	}
	v, e := s.SurfaceWaveSample(1, 0, 0)
	if e != nil || v[0] != 2 {
		t.Fatal(v, e)
	}
}
func TestFloatBodyBuoyancy(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, c := range []any{map[string]any{"op": "surface", "id": 1}, map[string]any{"op": "mesh", "triangles": []any{map[string]any{"a": []int{-10, 0, -10}, "b": []int{10, 0, -10}, "c": []int{0, 0, 10}, "surfaceId": 1}}}, map[string]any{"op": "float-body", "id": 1, "surfaceId": 1, "position": []int{0, -2, 0}, "mass": 1000, "radius": 1, "drag": 0}} {
		if _, e = s.Command(c); e != nil {
			t.Fatal(e)
		}
	}
	if e = s.AdvanceTo(8333); e != nil {
		t.Fatal(e)
	}
	body, e := s.FloatBody(1)
	expected := (9.81*4*math.Pi/3 - 9.81) / 120
	if e != nil || len(body) != 12 || math.Abs(body[4]-expected) > 1e-10 {
		t.Fatal(body, e)
	}
}

func TestSurfaceFoamBalance(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, c := range []any{map[string]any{"op": "surface", "id": 1}, map[string]any{"op": "mesh", "triangles": []any{map[string]any{"a": []int{-10, 0, -10}, "b": []int{10, 0, -10}, "c": []int{0, 0, 10}, "surfaceId": 1}}}, map[string]any{"op": "surface-waves", "surfaceId": 1, "waves": [][5]float64{{1, 1, 0, 0, 0}}}, map[string]any{"op": "surface-foam", "surfaceId": 1, "sourceRate": 2, "curvatureThreshold": 0, "decay": 1, "impactGain": 0}} {
		if _, e = s.Command(c); e != nil {
			t.Fatal(e)
		}
	}
	if e = s.AdvanceTo(8333); e != nil {
		t.Fatal(e)
	}
	rows, e := s.SurfaceFoam(1)
	if e != nil {
		t.Fatal(e)
	}
	r := rows[0]
	if math.Abs(r[1]-1.0/121) > 1e-12 || math.Abs(r[2]-r[1]-r[3]-r[4]) > 1e-12 {
		t.Fatal(r)
	}
}
