package nocturne

import (
	"encoding/json"
	"fmt"
	"strconv"
	"unicode/utf8"
)

// RenderFleetScene renders normalized version-1 Fleet scene JSON with the native
// core. It does not own the domain model, terminal, provider, or event loop.
// Inputs: at most 4 MiB of JSON from FleetController.compose(). Returns an owned
// Frame or a validation error. Unknown node fields are rejected.
// Example: frame, err := nocturne.RenderFleetScene(sceneBytes).
func RenderFleetScene(data []byte) (Frame, error) {
	var empty Frame
	if len(data) > 4*1024*1024 {
		return empty, fmt.Errorf("scene exceeds 4 MiB")
	}
	var scene struct {
		Version int
		Kind    string
		TimeMs  uint64
		Config  struct {
			Values                                   map[string]int32
			Palette, StarPalette, Glyphs, NovaGlyphs []string
		}
		Nodes  []map[string]json.RawMessage
		Events []struct {
			X, Y     float64
			Strength int32
			Kind     int32
			AtMs     uint64
			ID       int32
		}
	}
	if e := json.Unmarshal(data, &scene); e != nil {
		return empty, e
	}
	if scene.Version != 1 || scene.Kind != "nocturne.fleet.scene" {
		return empty, fmt.Errorf("Fleet scene version 1 required")
	}
	if len(scene.Nodes) > 512 || len(scene.Events) > 128 {
		return empty, fmt.Errorf("scene count bounds")
	}
	s, e := NewStudio()
	if e != nil {
		return empty, e
	}
	for k, v := range scene.Config.Values {
		if e = s.Set(k, v); e != nil {
			return empty, e
		}
	}
	for index, colors := range [][]string{scene.Config.Palette, scene.Config.StarPalette} {
		values := []uint32{}
		for _, v := range colors {
			if len(v) != 7 || v[0] != '#' {
				return empty, fmt.Errorf("RGB color required")
			}
			n, e := strconv.ParseUint(v[1:], 16, 24)
			if e != nil {
				return empty, e
			}
			values = append(values, uint32(n))
		}
		if e = s.SetColors(values, index == 1); e != nil {
			return empty, e
		}
	}
	for index, glyphs := range [][]string{scene.Config.Glyphs, scene.Config.NovaGlyphs} {
		values := []rune{}
		for _, g := range glyphs {
			if utf8.RuneCountInString(g) != 1 {
				return empty, fmt.Errorf("one scalar per glyph")
			}
			r, _ := utf8.DecodeRuneInString(g)
			values = append(values, r)
		}
		if e = s.SetGlyphs(values, index == 1); e != nil {
			return empty, e
		}
	}
	nodes := []StudioNode{}
	for _, raw := range scene.Nodes {
		var kind string
		geometry := [4]int32{}
		if e = json.Unmarshal(raw["kind"], &kind); e != nil {
			return empty, e
		}
		delete(raw, "kind")
		for i, k := range []string{"x", "y", "width", "height"} {
			if e = json.Unmarshal(raw[k], &geometry[i]); e != nil {
				return empty, e
			}
			delete(raw, k)
		}
		n, e := NewStudioNode(kind, geometry[0], geometry[1], geometry[2], geometry[3])
		if e != nil {
			return empty, e
		}
		for k, v := range raw {
			switch k {
			case "text":
				e = json.Unmarshal(v, &n.Text)
			case "data":
				e = json.Unmarshal(v, &n.Data)
			case "changedMs":
				var t uint64
				e = json.Unmarshal(v, &t)
				n.ChangedAt(t)
			default:
				var scalar int32
				e = json.Unmarshal(v, &scalar)
				if e == nil {
					e = n.Set(k, scalar)
				}
			}
			if e != nil {
				return empty, e
			}
		}
		nodes = append(nodes, n)
	}
	events := []StudioImpulse{}
	for _, v := range scene.Events {
		if v.X < -4096 || v.X > 4096 || v.Y < -4096 || v.Y > 4096 {
			return empty, fmt.Errorf("event coordinates")
		}
		events = append(events, StudioImpulse{XQ8: int32(v.X * 256), YQ8: int32(v.Y * 256), Strength: v.Strength, Kind: v.Kind, AtMs: v.AtMs, ID: v.ID})
	}
	return s.Render(scene.TimeMs, nodes, events)
}
