package nocturne

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"testing"
)

func TestStudioAcceptedReferences(t *testing.T) {
	raw, e := os.ReadFile("../../tests/studio.fixtures.json")
	if e != nil {
		t.Fatal(e)
	}
	var fixtures []struct {
		Name   string
		Config map[string]int32
		TimeMs uint64
		SHA256 string
		Nodes  []struct {
			Kind, Text                                     string
			X, Y, Width, Height, ID, Value, ColorAnimation int32
			Data                                           []int32
		}
		Events []struct {
			X, Y, Strength, Kind, ID int32
			AtMs                     uint64
		}
	}
	if e = json.Unmarshal(raw, &fixtures); e != nil {
		t.Fatal(e)
	}
	for _, c := range fixtures {
		t.Run(c.Name, func(t *testing.T) {
			s, _ := NewStudio()
			for k, v := range c.Config {
				if e := s.Set(k, v); e != nil {
					t.Fatal(e)
				}
			}
			nodes := []StudioNode{}
			for _, r := range c.Nodes {
				n, e := NewStudioNode(r.Kind, r.X, r.Y, r.Width, r.Height)
				if e != nil {
					t.Fatal(e)
				}
				n.Text = r.Text
				n.Data = r.Data
				n.Words[1] = r.ID
				n.Words[7] = r.Value
				n.Words[28] = r.ColorAnimation
				nodes = append(nodes, n)
			}
			events := []StudioImpulse{}
			for _, e := range c.Events {
				events = append(events, StudioImpulse{XQ8: e.X * 256, YQ8: e.Y * 256, Strength: e.Strength, Kind: e.Kind, AtMs: e.AtMs, ID: e.ID})
			}
			frame, e := s.Render(c.TimeMs, nodes, events)
			if e != nil {
				t.Fatal(e)
			}
			h := sha256.Sum256(frame.Bytes())
			if fmt.Sprintf("%x", h) != c.SHA256 {
				t.Fatalf("mismatch: %x", h)
			}
		})
	}
}
