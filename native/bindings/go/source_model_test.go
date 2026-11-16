package native

import (
	"bytes"
	"os"
	"testing"
)

func TestOriginalModelOwnedStorage(t *testing.T) {
	data, e := os.ReadFile("../../tests/fixtures/source-model/model-records.bin")
	if e != nil {
		t.Fatal(e)
	}
	a, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer a.Close()
	b, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer b.Close()
	if e = a.SetModelRecords(data); e != nil {
		t.Fatal(e)
	}
	copy, e := a.ModelRecords()
	if e != nil || !bytes.Equal(copy, data) {
		t.Fatal("model readback", e)
	}
	if _, e = a.Command(map[string]any{"op": "input", "text": string(bytes.Repeat([]byte("A🙂אב\n"), 14001))}); e != nil {
		t.Fatal(e)
	}
	snap, e := a.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	if e = b.Restore(snap); e != nil {
		t.Fatal(e)
	}
	copy, e = b.ModelRecords()
	if e != nil || !bytes.Equal(copy, data) {
		t.Fatal("restore", e)
	}
	bad := append([]byte(nil), data...)
	bad[39] = 1
	if a.SetModelRecords(bad) == nil {
		t.Fatal("bad RGB accepted")
	}
	after, e := a.Snapshot()
	if e != nil || !bytes.Equal(after, snap) {
		t.Fatal("non-atomic upload", e)
	}
	if e = a.SetModelRecords(nil); e != nil {
		t.Fatal(e)
	}
	copy, e = a.ModelRecords()
	if e != nil || len(copy) != 0 {
		t.Fatal("empty", e)
	}
	copy, e = b.ModelRecords()
	if e != nil || !bytes.Equal(copy, data) {
		t.Fatal("aliased", e)
	}
}
