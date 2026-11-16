package nocturne

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"strconv"
	"strings"
	"testing"
)

type Fixture struct {
	Name        string           `json:"name"`
	Values      map[string]int32 `json:"values"`
	TimeMs      uint64           `json:"timeMs"`
	Text        string           `json:"text"`
	Palette     []string         `json:"palette"`
	StarPalette []string         `json:"starPalette"`
	Glyphs      []string         `json:"glyphs"`
	SHA256      string           `json:"sha256"`
}

func colors(t *testing.T, values []string) []uint32 {
	t.Helper()
	result := []uint32{}
	for _, value := range values {
		n, err := strconv.ParseUint(strings.TrimPrefix(value, "#"), 16, 32)
		if err != nil {
			t.Fatal(err)
		}
		result = append(result, uint32(n))
	}
	return result
}

func TestCanonicalFrameParity(t *testing.T) {
	data, err := os.ReadFile("../../tests/fixtures.json")
	if err != nil {
		t.Fatal(err)
	}
	var fixtures []Fixture
	if err = json.Unmarshal(data, &fixtures); err != nil {
		t.Fatal(err)
	}
	for _, fixture := range fixtures {
		t.Run(fixture.Name, func(t *testing.T) {
			surface, err := NewSurface()
			if err != nil {
				t.Fatal(err)
			}
			for name, value := range fixture.Values {
				if err := surface.Set(name, value); err != nil {
					t.Fatal(err)
				}
			}
			if fixture.Palette != nil {
				if err := surface.SetPalette(colors(t, fixture.Palette)); err != nil {
					t.Fatal(err)
				}
			}
			if fixture.StarPalette != nil {
				if err := surface.SetStarPalette(colors(t, fixture.StarPalette)); err != nil {
					t.Fatal(err)
				}
			}
			if fixture.Glyphs != nil {
				glyphs := []rune{}
				for _, glyph := range fixture.Glyphs {
					glyphs = append(glyphs, []rune(glyph)[0])
				}
				if err := surface.SetGlyphs(glyphs); err != nil {
					t.Fatal(err)
				}
			}
			frame, err := surface.Render(fixture.TimeMs, fixture.Text)
			if err != nil {
				t.Fatal(err)
			}
			hash := sha256.Sum256(frame.Bytes())
			if hex.EncodeToString(hash[:]) != fixture.SHA256 {
				t.Fatalf("canonical hash mismatch")
			}
		})
	}
}
func TestInvalidConfiguration(t *testing.T) {
	s, err := NewSurface()
	if err != nil {
		t.Fatal(err)
	}
	for _, item := range []struct {
		name  string
		value int32
	}{{"width", -1}, {"height", 257}, {"unknown", 3}, {"gradientPeriodMs", 0}} {
		if s.Set(item.name, item.value) == nil {
			t.Fatalf("accepted invalid %+v", item)
		}
	}
	if s.SetPalette(nil) == nil {
		t.Fatal("accepted empty palette")
	}
	if s.SetStarPalette([]uint32{0xffffffff}) == nil {
		t.Fatal("accepted invalid color")
	}
	if _, err := s.Render(0, strings.Repeat("x", 513)); err == nil {
		t.Fatal("accepted oversized text")
	}
}
func TestFrameHistoryDoesNotMatter(t *testing.T) {
	s, err := NewSurface()
	if err != nil {
		t.Fatal(err)
	}
	a, _ := s.Render(5000, "a")
	s.Render(9000, "b")
	b, _ := s.Render(5000, "a")
	if sha256.Sum256(a.Bytes()) != sha256.Sum256(b.Bytes()) {
		t.Fatal("render mutates prior frame")
	}
}
