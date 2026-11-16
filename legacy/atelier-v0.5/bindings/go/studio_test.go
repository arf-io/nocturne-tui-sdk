package nocturne

import (
	"bytes"
	"testing"
)

func TestStudioParityAndOwnership(t *testing.T) {
	s, e := NewStudio()
	if e != nil {
		t.Fatal(e)
	}
	_ = s.Set("width", 40)
	_ = s.Set("height", 12)
	n, _ := NewStudioNode("text", 2, 3, 30, 1)
	n.Text = "hello"
	a, e := s.Render(1234, []StudioNode{n}, nil)
	if e != nil {
		t.Fatal(e)
	}
	before := a.Bytes()
	_, _ = s.Render(8000, nil, nil)
	b, _ := s.Render(1234, []StudioNode{n}, nil)
	if !bytes.Equal(before, b.Bytes()) || !bytes.Equal(before, a.Bytes()) {
		t.Fatal("replay/ownership")
	}
}
func TestStudioAllPrimitives(t *testing.T) {
	s, _ := NewStudio()
	for _, kind := range []string{"text", "box", "rule", "button", "item", "cursor", "progress", "bars", "pie", "donut", "scatter", "line", "digits", "edge"} {
		n, _ := NewStudioNode(kind, 2, 2, 30, 10)
		n.Text = "67"
		n.Data = []int32{200, 400, 700, 900}
		n.Words[7] = 670
		if _, e := s.Render(5000, []StudioNode{n}, nil); e != nil {
			t.Fatalf("%s: %v", kind, e)
		}
	}
}
func TestStudioHitAndDisabled(t *testing.T) {
	s, _ := NewStudio()
	n, _ := NewStudioNode("button", 2, 2, 10, 3)
	n.Words[1] = 7
	h, e := s.Hit([]StudioNode{n}, 3, 3)
	if e != nil || h == nil || h.ID != 7 {
		t.Fatal(h, e)
	}
	n.Words[6] = 3
	h, e = s.Hit([]StudioNode{n}, 3, 3)
	if e != nil || h != nil {
		t.Fatal(h, e)
	}
}
func TestStudioValidation(t *testing.T) {
	s, _ := NewStudio()
	if s.Set("width", -1) == nil {
		t.Fatal("negative width")
	}
	if s.SetColors([]uint32{0x1000000}, false) == nil {
		t.Fatal("invalid RGB")
	}
	if s.SetGlyphs([]rune{0xd800}, false) == nil {
		t.Fatal("surrogate")
	}
	n, _ := NewStudioNode("text", 0, 0, -1, 2)
	if _, e := s.Render(0, []StudioNode{n}, nil); e == nil {
		t.Fatal("invalid node")
	}
}
func TestStudioCompositorTween(t *testing.T) {
	s, _ := NewStudio()
	a, _ := s.Render(0, nil, nil)
	b, _ := s.Render(500, nil, nil)
	c, e := s.Composite(a, b, 0, 0, 0, 0)
	if e != nil || !bytes.Equal(a.Bytes(), c.Bytes()) {
		t.Fatal("zero opacity")
	}
	for ease := int32(0); ease < 4; ease++ {
		v, e := StudioTween(0, 670, 1000, 1000, ease)
		if e != nil || v != 670 {
			t.Fatal(v, e)
		}
	}
}
