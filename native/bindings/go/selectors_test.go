package native

import (
	"bytes"
	"encoding/json"
	"testing"
)

// TestSelectorRestoresAuthoring exercises C state without a replacement renderer.
func TestSelectorRestoresAuthoring(t *testing.T) {
	scene, err := New(2030)
	if err != nil {
		t.Fatal(err)
	}
	defer scene.Close()
	command := func(raw string) {
		t.Helper()
		if _, err := scene.CommandRaw([]byte(raw)); err != nil {
			t.Fatal(err)
		}
	}
	snapshot := func() []byte {
		t.Helper()
		raw, err := scene.Snapshot()
		if err != nil {
			t.Fatal(err)
		}
		return raw
	}
	command(`{"op":"widget","id":1,"kind":"button","x":8,"y":8,"width":30,"height":3,"text":"Go state","material":1,"alpha":0.2}`)
	command(`{"op":"state-register","id":1,"path":"/go/control","role":"control","target":{"family":"widget","id":1}}`)
	command(`{"op":"style-rule","id":1,"selector":{"family":"widget"},"style":{"material":2,"alpha":0.8}}`)
	command(`{"op":"widget","id":1,"material":3,"alpha":0.4}`)
	before := snapshot()
	if _, err := scene.Render(); err != nil {
		t.Fatal(err)
	}
	if _, err := scene.Info(); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(before, snapshot()) {
		t.Fatal("appearance render mutated state")
	}
	command(`{"op":"remove-style-rule","id":1}`)
	raw, err := scene.Info()
	if err != nil {
		t.Fatal(err)
	}
	var info struct {
		RegisteredStates []struct {
			Effective struct {
				Material float64
				Alpha    float64
			}
		}
	}
	if err = json.Unmarshal(raw, &info); err != nil {
		t.Fatal(err)
	}
	if len(info.RegisteredStates) != 1 || info.RegisteredStates[0].Effective.Material != 3 || info.RegisteredStates[0].Effective.Alpha != 0.4 {
		t.Fatal("latest authored appearance was not restored")
	}
	before = snapshot()
	if _, err = scene.CommandRaw([]byte(`{"op":"style-rule","id":1,"selector":{"family":"widget"},"style":{"material":200}}`)); err == nil {
		t.Fatal("invalid material accepted")
	}
	if !bytes.Equal(before, snapshot()) {
		t.Fatal("rejected rule modified state")
	}
}
