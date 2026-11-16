package native

import (
	"bytes"
	"encoding/json"
	"os"
	"testing"
)

func TestScenicCompositionsUseCurrentNativeCore(t *testing.T) {
	for _, name := range []string{"waterfall", "road", "garden"} {
		t.Run(name, func(t *testing.T) {
			raw, e := os.ReadFile("../../examples/" + name + "-scene.json")
			if e != nil {
				t.Fatal(e)
			}
			var fixture struct {
				Commands []json.RawMessage `json:"commands"`
			}
			if e = json.Unmarshal(raw, &fixture); e != nil {
				t.Fatal(e)
			}
			batch, e := json.Marshal(struct {
				Op       string            `json:"op"`
				Commands []json.RawMessage `json:"commands"`
			}{"batch", fixture.Commands})
			if e != nil {
				t.Fatal(e)
			}
			s, e := New(42)
			if e != nil {
				t.Fatal(e)
			}
			defer s.Close()
			if _, e = s.CommandRaw(batch); e != nil {
				t.Fatal(e)
			}
			if e = s.AdvanceTo(1000000); e != nil {
				t.Fatal(e)
			}
			before, e := s.Snapshot()
			if e != nil {
				t.Fatal(e)
			}
			info, e := s.InfoComplete()
			if e != nil || !json.Valid(info) {
				t.Fatal("invalid owned info", e)
			}
			if _, e = s.Render(); e != nil {
				t.Fatal(e)
			}
			after, e := s.Snapshot()
			if e != nil || !bytes.Equal(before, after) {
				t.Fatal("query/render mutation", e)
			}
			if name == "road" {
				var q struct{ Camera struct{ Position []float64 } }
				json.Unmarshal(info, &q)
				if len(q.Camera.Position) != 3 || q.Camera.Position[2] != -2 {
					t.Fatal(q)
				}
			}
			if name == "waterfall" {
				var q struct {
					Flows []struct{ DeliveredVolume float64 }
				}
				json.Unmarshal(info, &q)
				if len(q.Flows) != 1 || q.Flows[0].DeliveredVolume != 1 {
					t.Fatal(q)
				}
			}
		})
	}
}
