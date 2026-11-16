package nocturne

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"testing"
)

func TestFleetFixtures(t *testing.T) {
	data, e := os.ReadFile("../../tests/fleet/fixtures.json")
	if e != nil {
		t.Fatal(e)
	}
	var corpus struct {
		Fixtures []struct {
			Name   string
			Scene  json.RawMessage
			Sha256 string
		}
		Fades []struct {
			Args  []int64
			Value int32
		}
	}
	if e = json.Unmarshal(data, &corpus); e != nil {
		t.Fatal(e)
	}
	for _, f := range corpus.Fixtures {
		t.Run(f.Name, func(t *testing.T) {
			frame, e := RenderFleetScene(f.Scene)
			if e != nil {
				t.Fatal(e)
			}
			if got := fmt.Sprintf("%x", sha256.Sum256(frame.Bytes())); got != f.Sha256 {
				t.Fatal(got, f.Sha256)
			}
		})
	}
	for _, f := range corpus.Fades {
		a := f.Args
		got, e := FleetInkOpacity(uint32(a[0]), uint32(a[1]), int32(a[2]), int32(a[3]), int32(a[4]))
		if e != nil || got != f.Value {
			t.Fatal(f, got, e)
		}
	}
}
func TestFleetOpacityReject(t *testing.T) {
	if _, e := FleetInkOpacity(0, 0, 0, -1, 760); e == nil {
		t.Fatal("negative band")
	}
	if _, e := FleetInkOpacity(0, 0, 0, 0, 1001); e == nil {
		t.Fatal("minimum")
	}
	if _, e := RenderFleetScene([]byte(`{"version":2}`)); e == nil {
		t.Fatal("scene version")
	}
}
