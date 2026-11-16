// Studio is the additive Nocturne v2 material and widget API.
package nocturne

/*
#cgo CFLAGS: -std=c11 -O3 -I${SRCDIR}/../../include
#include "nocturne_studio.h"
*/
import "C"
import (
	"fmt"
	"unsafe"
)

// Studio owns configuration, not time or terminal I/O. Use separate instances
// for concurrent mutations. Render returns owned snapshots.
type Studio struct{ config C.NsStageConfig }

// StudioNode is a flat primitive plus owned text/data. Words follow NsNodeKey.
// Prefer NewStudioNode for correct defaults; advanced users may edit Words.
type StudioNode struct {
	Words [32]int32
	Text  string
	Data  []int32
}

// StudioImpulse is a deterministic event. XQ8/YQ8 are cell coordinates * 256.
type StudioImpulse struct {
	XQ8, YQ8, Strength, Kind int32
	AtMs                     uint64
	ID                       int32
}

// StudioHit identifies a semantic node and chart sample/segment.
type StudioHit struct{ ID, Item int32 }

// NewStudio verifies ABI layout and initializes all bytes. It returns an error
// on incompatible library linkage. Example: stage, err := NewStudio().
func NewStudio() (*Studio, error) {
	if C.nsStageVersion() != 2 || C.nsStageConfigSize() != 704 || unsafe.Sizeof(Cell{}) != 16 {
		return nil, fmt.Errorf("Studio ABI mismatch")
	}
	s := &Studio{}
	C.nsStageDefaults(&s.config)
	return s, nil
}

// Set changes a named integer field atomically. Unknown/out-of-range keys return
// an error. Example: stage.Set("focusMode", 3).
func (s *Studio) Set(name string, value int32) error {
	f, ok := STUDIO_FIELDS[name]
	if !ok {
		return fmt.Errorf("unknown Studio field: %s", name)
	}
	if value < f.minimum || value > f.maximum {
		return fmt.Errorf("%s: %d..%d", name, f.minimum, f.maximum)
	}
	s.config.values[f.index] = C.int32_t(value)
	return nil
}

// SetColors replaces a 1..32 stop palette. star selects peak star colors.
// Invalid input is rejected without changing the previous palette.
func (s *Studio) SetColors(colors []uint32, star bool) error {
	if len(colors) < 1 || len(colors) > 32 {
		return fmt.Errorf("1..32 colors required")
	}
	for _, v := range colors {
		if v > 0xffffff {
			return fmt.Errorf("invalid RGB")
		}
	}
	for i, v := range colors {
		if star {
			s.config.starPalette[i] = C.uint32_t(v)
		} else {
			s.config.palette[i] = C.uint32_t(v)
		}
	}
	if star {
		return s.Set("starColorCount", int32(len(colors)))
	}
	return s.Set("paletteCount", int32(len(colors)))
}

// SetGlyphs supplies a custom ordinary/nova scalar set. Native rendering uses
// a documented single-cell glyph profile. Unsupported glyphs become '?'.
func (s *Studio) SetGlyphs(glyphs []rune, nova bool) error {
	limit := 32
	if nova {
		limit = 16
	}
	if len(glyphs) < 1 || len(glyphs) > limit {
		return fmt.Errorf("1..%d glyphs required", limit)
	}
	for _, g := range glyphs {
		if g < 0 || g > 0x10ffff || (g >= 0xd800 && g <= 0xdfff) {
			return fmt.Errorf("invalid scalar")
		}
	}
	for i, g := range glyphs {
		if nova {
			s.config.novaGlyphs[i] = C.uint32_t(g)
		} else {
			s.config.glyphs[i] = C.uint32_t(g)
		}
	}
	if nova {
		return s.Set("novaGlyphCount", int32(len(glyphs)))
	}
	return s.Set("starGlyphCount", int32(len(glyphs)))
}

// NewStudioNode builds one of 14 primitive kinds with safe default style values.
// Errors: unknown kind. Geometry is validated on Render/Hit. Example:
// n, err := NewStudioNode("progress",2,3,30,1); n.Words[7]=670.
func NewStudioNode(kind string, x, y, width, height int32) (StudioNode, error) {
	names := []string{"text", "box", "rule", "button", "item", "cursor", "progress", "bars", "pie", "donut", "scatter", "line", "digits", "edge"}
	index := -1
	for i, name := range names {
		if name == kind {
			index = i
			break
		}
	}
	if index < 0 {
		return StudioNode{}, fmt.Errorf("unknown node kind %q", kind)
	}
	n := StudioNode{}
	n.Words[0] = int32(index)
	n.Words[2] = x
	n.Words[3] = y
	n.Words[4] = width
	n.Words[5] = height
	n.Words[12] = 0xe2d9c9
	n.Words[13] = 0x11100e
	n.Words[14] = 1000
	n.Words[21] = 17
	n.Words[22] = 24
	n.Words[26] = 620
	n.Words[27] = 830
	n.Words[30] = 1
	return n, nil
}
func packStudioNodes(nodes []StudioNode) ([]C.NsNode, []C.uint32_t, []C.int32_t, error) {
	if len(nodes) > 512 {
		return nil, nil, nil, fmt.Errorf("512 node limit")
	}
	ns := make([]C.NsNode, len(nodes))
	var text []C.uint32_t
	var data []C.int32_t
	for i, n := range nodes {
		for j, v := range n.Words {
			ns[i].values[j] = C.int32_t(v)
		}
		points := []rune(n.Text)
		ns[i].values[17] = C.int32_t(len(text))
		ns[i].values[18] = C.int32_t(len(points))
		ns[i].values[19] = C.int32_t(len(data))
		ns[i].values[20] = C.int32_t(len(n.Data))
		if len(text)+len(points) > 32768 || len(data)+len(n.Data) > 16384 {
			return nil, nil, nil, fmt.Errorf("scene capacity")
		}
		for _, p := range points {
			text = append(text, C.uint32_t(p))
		}
		for _, v := range n.Data {
			if v < -1000000 || v > 1000000 {
				return nil, nil, nil, fmt.Errorf("data out of bounds")
			}
			data = append(data, C.int32_t(v))
		}
	}
	return ns, text, data, nil
}
func ptr[T any](v []T) *T {
	if len(v) == 0 {
		return nil
	}
	return &v[0]
}

// Render evaluates timeMs and ordered impulses/nodes. No pointer is retained by C.
// Errors return no partial frame. Data can change at the same timeMs independently
// of the host's decorative animation deadline.
func (s *Studio) Render(timeMs uint64, nodes []StudioNode, events []StudioImpulse) (Frame, error) {
	if len(events) > 128 {
		return Frame{}, fmt.Errorf("128 impulse limit")
	}
	ns, text, data, err := packStudioNodes(nodes)
	if err != nil {
		return Frame{}, err
	}
	ev := make([]C.NsImpulse, len(events))
	for i, e := range events {
		v := [8]int32{e.XQ8, e.YQ8, e.Strength, e.Kind, int32(uint32(e.AtMs)), int32(uint32(e.AtMs >> 32)), e.ID, 0}
		for j, x := range v {
			ev[i].values[j] = C.int32_t(x)
		}
	}
	width, height := int(s.config.values[0]), int(s.config.values[1])
	cells := make([]Cell, width*height)
	result := C.nsStageRender(&s.config, C.uint64_t(timeMs), ptr(ev), C.uint32_t(len(ev)), ptr(ns), C.uint32_t(len(ns)), ptr(text), C.uint32_t(len(text)), ptr(data), C.uint32_t(len(data)), (*C.NsCell)(unsafe.Pointer(ptr(cells))), C.uint32_t(len(cells)))
	if result < 0 {
		return Frame{}, fmt.Errorf("Studio renderer error %d", result)
	}
	return Frame{width, height, cells}, nil
}

// Hit performs reverse-z geometric picking. A disabled node blocks underlying
// nodes. nil result means no hit; malformed geometry returns an error.
func (s *Studio) Hit(nodes []StudioNode, x, y int32) (*StudioHit, error) {
	ns, _, data, err := packStudioNodes(nodes)
	if err != nil {
		return nil, err
	}
	v := C.nsStageHit(ptr(ns), C.uint32_t(len(ns)), ptr(data), C.uint32_t(len(data)), C.int32_t(x), C.int32_t(y))
	if v < 0 {
		return nil, fmt.Errorf("invalid hit inputs")
	}
	if v == 0 {
		return nil, nil
	}
	return &StudioHit{nodes[(int(v)>>16)-1].Words[1], int32(v&65535) - 1}, nil
}

// Composite returns an owned source-over result. Inputs are never mutated.
// Cells are flattened where text replaces half-block geometry; opacity 0..1000.
func (s *Studio) Composite(dest, source Frame, x, y, fgOpacity, bgOpacity int32) (Frame, error) {
	for _, f := range []Frame{dest, source} {
		if f.Width < 0 || f.Width > 512 || f.Height < 0 || f.Height > 256 || len(f.Cells) != f.Width*f.Height {
			return Frame{}, fmt.Errorf("invalid frame")
		}
	}
	cells := append([]Cell(nil), dest.Cells...)
	v := C.nsStageComposite((*C.NsCell)(unsafe.Pointer(ptr(cells))), C.int32_t(dest.Width), C.int32_t(dest.Height), (*C.NsCell)(unsafe.Pointer(ptr(source.Cells))), C.int32_t(source.Width), C.int32_t(source.Height), C.int32_t(x), C.int32_t(y), C.int32_t(fgOpacity), C.int32_t(bgOpacity))
	if v < 0 {
		return Frame{}, fmt.Errorf("invalid composition")
	}
	return Frame{dest.Width, dest.Height, cells}, nil
}

// StudioTween is pure scalar interpolation. Easing 0 linear,1 smoothstep,2 sine,
// 3 cubic-out. Zero duration immediately returns the target.
func StudioTween(from, to int32, elapsed uint64, duration uint32, easing int32) (int32, error) {
	if easing < 0 || easing > 3 {
		return 0, fmt.Errorf("easing 0..3 required")
	}
	return int32(C.nsStageTween(C.int32_t(from), C.int32_t(to), C.uint64_t(elapsed), C.uint32_t(duration), C.int32_t(easing))), nil
}

// Set applies one semantic node property. Unknown/reserved fields return an
// error. Full range validation is atomic at Render before any cells are written.
// Example: node.Set("value",670); node.Set("colorAnimation",2).
func (n *StudioNode) Set(name string, value int32) error {
	keys := map[string]int{"id": 1, "state": 6, "value": 7, "fromValue": 8, "durationMs": 11, "fg": 12, "bg": 13, "fgOpacity": 14, "bgOpacity": 15, "style": 16, "hueStep": 21, "hueSpeed": 22, "hueBase": 23, "revealMs": 24, "hueSaturation": 26, "hueBrightness": 27, "colorAnimation": 28, "glyph": 29, "zoom": 30}
	index, ok := keys[name]
	if !ok {
		return fmt.Errorf("unknown/reserved node field %q", name)
	}
	n.Words[index] = value
	return nil
}

// ChangedAt sets the explicit start of a scalar/reveal transition.
func (n *StudioNode) ChangedAt(timeMs uint64) {
	n.Words[9] = int32(uint32(timeMs))
	n.Words[10] = int32(uint32(timeMs >> 32))
}

// FleetInkOpacity returns arrival × top-horizon opacity (0..1000).
// Times are unsigned milliseconds. Positions are cells*256. A zero fade or band
// disables that effect. Invalid band/minimum returns an error without mutation.
// Example: FleetInkOpacity(420, 420, 768, 1536, 760) returns 880, nil.
func FleetInkOpacity(ageMs, fadeMs uint32, rowQ8, bandQ8, topMinimum int32) (int32, error) {
	if bandQ8 < 0 || topMinimum < 0 || topMinimum > 1000 {
		return 0, fmt.Errorf("invalid Fleet opacity bounds")
	}
	return int32(C.nsFleetInkOpacity(C.uint32_t(ageMs), C.uint32_t(fadeMs), C.int32_t(rowQ8), C.int32_t(bandQ8), C.int32_t(topMinimum))), nil
}

// OklchColor returns gamut-mapped sRGB from L/1000, C/10000, h/1000 degrees.
// Chroma is reduced at fixed L/h. It does not use a clock or retain state.
// Example: color, err := OklchColor(700, 1200, 270000).
func OklchColor(lightness, chroma, hueMilliDegrees int32) (uint32, error) {
	if lightness < 0 || lightness > 1000 || chroma < 0 || chroma > 4000 {
		return 0, fmt.Errorf("OKLCh L=0..1000 and C=0..4000 required")
	}
	return uint32(C.nsOklchColor(C.int32_t(lightness), C.int32_t(chroma), C.int32_t(hueMilliDegrees))), nil
}

// OklchLightness returns Oklab L * 1000 for 24-bit sRGB.
func OklchLightness(color uint32) (int32, error) {
	if color > 0xffffff {
		return 0, fmt.Errorf("24-bit RGB required")
	}
	return int32(C.nsOklchLightness(C.uint32_t(color))), nil
}
