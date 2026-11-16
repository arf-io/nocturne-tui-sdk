// Package nocturne exposes the portable Nocturne cell-material renderer.
// It owns neither an event loop nor a terminal. CGO and a C compiler are required.
package nocturne

/*
#cgo CFLAGS: -std=c11 -O3 -I${SRCDIR}/../../include
#include "nocturne.h"
*/
import "C"

import (
	"encoding/binary"
	"fmt"
	"unsafe"
)

// Cell contains a Unicode code point, packed RGB colors, and reserved flags.
// Its 16-byte layout matches the versioned native ABI.
type Cell struct{ Glyph, Fg, Bg, Flags uint32 }

// Frame owns an independent, row-major cell slice.
type Frame struct {
	Width, Height int
	Cells         []Cell
}

// Bytes returns canonical little-endian bytes, independent of the host endian.
func (frame Frame) Bytes() []byte {
	result := make([]byte, len(frame.Cells)*16)
	for index, cell := range frame.Cells {
		for field, value := range [...]uint32{cell.Glyph, cell.Fg, cell.Bg, cell.Flags} {
			binary.LittleEndian.PutUint32(result[index*16+field*4:], value)
		}
	}
	return result
}

// Surface holds mutable settings. Do not mutate or render the same Surface
// concurrently. Separate Surface instances can be rendered concurrently.
type Surface struct{ config C.NsConfig }

// NewSurface initializes validated native defaults; it has no terminal effects.
// Example: s, err := NewSurface(); err = s.Set("effect", 5).
func NewSurface() (*Surface, error) {
	if C.nsAbiVersion() != 1 || C.nsConfigSize() != 448 || C.nsCellSize() != 16 || unsafe.Sizeof(Cell{}) != 16 {
		return nil, fmt.Errorf("Nocturne ABI mismatch")
	}
	s := &Surface{}
	C.nsDefaultConfig(&s.config)
	return s, nil
}

// Set changes one named integer setting. Unknown names and out-of-range values
// return an error without changing the previous setting.
func (s *Surface) Set(name string, value int32) error {
	field, ok := FIELDS[name]
	if !ok {
		return fmt.Errorf("unknown setting: %s", name)
	}
	if value < field.minimum || value > field.maximum {
		return fmt.Errorf("%s must be %d..%d", name, field.minimum, field.maximum)
	}
	s.config.values[field.index] = C.int32_t(value)
	return nil
}

// SetPalette replaces gradient stops with 1..8 packed RGB values.
func (s *Surface) SetPalette(colors []uint32) error {
	if err := validatePalette(colors); err != nil {
		return err
	}
	for index, color := range colors {
		s.config.palette[index] = C.uint32_t(color)
	}
	return s.Set("paletteCount", int32(len(colors)))
}

// SetStarPalette replaces the 1..8 predefined peak star colors.
func (s *Surface) SetStarPalette(colors []uint32) error {
	if err := validatePalette(colors); err != nil {
		return err
	}
	for index, color := range colors {
		s.config.starPalette[index] = C.uint32_t(color)
	}
	return s.Set("starPaletteCount", int32(len(colors)))
}

func validatePalette(colors []uint32) error {
	if len(colors) < 1 || len(colors) > 8 {
		return fmt.Errorf("a palette needs 1..8 colors")
	}
	for _, color := range colors {
		if color > 0xffffff {
			return fmt.Errorf("color exceeds 24-bit RGB")
		}
	}
	return nil
}

// SetGlyphs supplies 1..32 custom star code points. Unsupported glyphs are
// replaced by '?' in the demo renderer, including terminal control characters.
func (s *Surface) SetGlyphs(glyphs []rune) error {
	if len(glyphs) < 1 || len(glyphs) > 32 {
		return fmt.Errorf("expected 1..32 glyphs")
	}
	for _, glyph := range glyphs {
		if glyph < 0 || glyph > 0x10ffff {
			return fmt.Errorf("invalid Unicode scalar")
		}
	}
	for index, glyph := range glyphs {
		s.config.glyphs[index] = C.uint32_t(glyph)
	}
	_ = s.Set("glyphCount", int32(len(glyphs)))
	return s.Set("glyphSet", 4)
}

// Render produces an owned frame at an explicit motion timestamp in milliseconds.
// Calling it again with the same time and new text/data updates immediately while
// decorative motion stays fixed. Text is limited to 512 Unicode code points.
// Example: frame, err := s.Render(5000, "immediate text").
func (s *Surface) Render(motionMs uint64, text string) (Frame, error) {
	points := []rune(text)
	if len(points) > 512 {
		return Frame{}, fmt.Errorf("text exceeds 512 code points")
	}
	width, height := int(s.config.values[0]), int(s.config.values[1])
	cells := make([]Cell, width*height)
	var cellPtr *C.NsCell
	if len(cells) > 0 {
		cellPtr = (*C.NsCell)(unsafe.Pointer(&cells[0]))
	}
	// A non-null pointer with length zero distinguishes an empty string from
	// the C renderer's NULL-pointer request for default demonstration text.
	codePoints := make([]C.uint32_t, len(points)+1)
	for index, glyph := range points {
		codePoints[index] = C.uint32_t(glyph)
	}
	count := C.nsRender(&s.config, C.uint64_t(motionMs), &codePoints[0], C.uint32_t(len(points)), cellPtr, C.uint32_t(len(cells)))
	if count < 0 {
		return Frame{}, fmt.Errorf("renderer returned %d", int32(count))
	}
	return Frame{width, height, cells}, nil
}
