package native

import (
	"bytes"
	"encoding/binary"
	"testing"
)

func TestCellArt(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	_, e = s.CommandRaw([]byte(`{"op":"cell-art","id":1,"width":1,"height":1,"x":2,"y":2,"layer":"overlay","cells":[[65,16711680,255]]}`))
	if e != nil {
		t.Fatal(e)
	}
	saved, e := s.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	f, e := s.Render()
	if e != nil {
		t.Fatal(e)
	}
	at := (2*int(f.Width) + 2) * 16
	if binary.LittleEndian.Uint32(f.Bytes[at:]) != 65 || binary.LittleEndian.Uint32(f.Bytes[at+4:]) != 16711680 || binary.LittleEndian.Uint32(f.Bytes[at+8:]) != 255 {
		t.Fatal("cell art mismatch")
	}
	after, e := s.Snapshot()
	if e != nil || !bytes.Equal(saved, after) {
		t.Fatal("render mutation", e)
	}
}
