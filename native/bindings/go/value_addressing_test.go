package native

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"testing"
)

func TestValueAddressing(t *testing.T) {
	s, e := New(42)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, command := range []string{`{"op":"define","path":"/projection","value":60,"binding":{"family":"camera","field":"fov"}}`, `{"op":"set","path":"/projection","value":50}`} {
		if _, e = s.CommandRaw([]byte(command)); e != nil {
			t.Fatal(e)
		}
	}
	raw, e := s.Info()
	if e != nil {
		t.Fatal(e)
	}
	var info struct {
		Camera struct {
			Fov float64 `json:"fov"`
		}
	}
	if e = json.Unmarshal(raw, &info); e != nil || info.Camera.Fov != 50 {
		t.Fatal("camera projection binding", e)
	}
	before, e := s.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	if _, e = s.CommandRaw([]byte(`{"op":"set","path":"/projection","value":151}`)); e == nil {
		t.Fatal("accepted invalid fov")
	}
	after, e := s.Snapshot()
	if e != nil || !bytes.Equal(before, after) {
		t.Fatal("rejection mutated state", e)
	}
}

func TestMaterialLightnessBinding(t *testing.T) {
	s, e := New(42)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	for _, command := range []string{`{"op":"material","id":2,"space":"hsl","channels":{"h":0,"s":1,"l":0.5},"alpha":1}`, `{"op":"widget","id":1,"kind":"text","x":2,"y":2,"height":1,"text":"A","alpha":0,"material":2}`, `{"op":"define","path":"/light","value":0.25,"binding":{"family":"material","id":2,"field":"lightness"}}`} {
		if _, e = s.CommandRaw([]byte(command)); e != nil {
			t.Fatal(e)
		}
	}
	f, e := s.Render()
	if e != nil {
		t.Fatal(e)
	}
	if binary.LittleEndian.Uint32(f.Bytes[(2*int(f.Width)+2)*16+4:]) != 0x800000 {
		t.Fatal("HSL lightness changed the wrong channel")
	}
}
