package native

/*
#include "nocturne_native.h"
*/
import "C"
import (
	"errors"
	"unicode/utf8"
)

func documentScalars(text string) ([]C.uint32_t, error) {
	if !utf8.ValidString(text) {
		return nil, errors.New("invalid Unicode")
	}
	count := utf8.RuneCountInString(text)
	if uint64(count) > 0x7fffffff {
		return nil, errors.New("native scalar addressability")
	}
	values := make([]C.uint32_t, max(1, count))
	i := 0
	for _, r := range text {
		values[i] = C.uint32_t(r)
		i++
	}
	return values, nil
}
func documentWords(count, multiplier int) ([]C.uint32_t, error) {
	if count < 0 || count > int(^uint(0)>>1)/multiplier {
		return nil, errors.New("document allocation addressability")
	}
	return make([]C.uint32_t, max(1, count*multiplier)), nil
}

// DocumentLayout retains full-paragraph native bidi with caller-owned workspace.
func (s *Scene) DocumentLayout(text string, columns, direction, ambiguous uint32) ([][7]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	if columns == 0 || direction > 2 || (ambiguous != 1 && ambiguous != 2) {
		return nil, errors.New("invalid document policy")
	}
	values, e := documentScalars(text)
	if e != nil {
		return nil, e
	}
	count := utf8.RuneCountInString(text)
	out, e := documentWords(count, 7)
	if e != nil {
		return nil, e
	}
	scratch, e := documentWords(count+1, 40)
	if e != nil {
		return nil, e
	}
	n := C.nrDocumentBidiClusterLayout(&values[0], C.uint32_t(count), C.uint32_t(ambiguous), C.uint32_t(columns), C.uint32_t(direction), &out[0], C.uint32_t(count), &scratch[0], C.uint64_t(len(scratch)))
	if n < 0 {
		return nil, errors.New("invalid document layout")
	}
	rows := make([][7]uint32, int(n))
	for i := range rows {
		for j := range rows[i] {
			rows[i][j] = uint32(out[i*7+j])
		}
	}
	return rows, nil
}

// DocumentBoundaries includes clusters hidden by the bidi X9 removal rule.
func (s *Scene) DocumentBoundaries(text string) ([]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	values, e := documentScalars(text)
	if e != nil {
		return nil, e
	}
	count := utf8.RuneCountInString(text)
	out, e := documentWords(count+1, 1)
	if e != nil {
		return nil, e
	}
	n := C.nrGraphemeBreaks(&values[0], C.uint32_t(count), &out[0], C.uint32_t(len(out)))
	if n < 0 {
		return nil, errors.New("invalid Unicode")
	}
	rows := make([]uint32, int(n))
	for i := range rows {
		rows[i] = uint32(out[i])
	}
	return rows, nil
}
func documentEdge(text []rune, row [7]uint32, end int) [3]uint32 {
	scalar := text[row[0]]
	newline := scalar == 10 || scalar == 11 || scalar == 12 || scalar == 13 || scalar == 0x85 || scalar == 0x2028 || scalar == 0x2029
	x, y := row[2], row[3]
	if newline {
		if end == 1 {
			x = 0
			y++
		}
	} else if (row[5]&1 == 1 && end == 0) || (row[5]&1 == 0 && end == 1) {
		x += row[4]
	}
	return [3]uint32{x, y, row[5]}
}
func documentDistance(a, b uint32) uint64 {
	if a > b {
		return uint64(a) - uint64(b)
	}
	return uint64(b) - uint64(a)
}

// DocumentHit uses the same nearest-edge and largest-offset tie breaks as BidiHit.
func (s *Scene) DocumentHit(text string, columns, column, row, direction, ambiguous uint32) (uint32, error) {
	rows, e := s.DocumentLayout(text, columns, direction, ambiguous)
	if e != nil {
		return 0, e
	}
	source := []rune(text)
	selected := uint32(0)
	bestY, bestX := ^uint64(0), ^uint64(0)
	for _, r := range rows {
		for end := 0; end < 2; end++ {
			edge := documentEdge(source, r, end)
			y, x := documentDistance(edge[1], row), documentDistance(edge[0], column)
			if y < bestY || (y == bestY && (x < bestX || (x == bestX && r[end] > selected))) {
				bestY, bestX, selected = y, x, r[end]
			}
		}
	}
	return selected, nil
}
func (s *Scene) DocumentCaret(text string, columns, offset, affinity, direction, ambiguous uint32) ([3]uint32, error) {
	rows, e := s.DocumentLayout(text, columns, direction, ambiguous)
	if e != nil {
		return [3]uint32{}, e
	}
	bounds, e := s.DocumentBoundaries(text)
	if e != nil {
		return [3]uint32{}, e
	}
	valid := false
	for _, b := range bounds {
		if b == offset {
			valid = true
			break
		}
	}
	if !valid || affinity > 1 {
		return [3]uint32{}, errors.New("invalid caret offset or affinity")
	}
	source := []rune(text)
	chosen := [3]uint32{}
	if direction == 1 {
		chosen[2] = 1
	}
	found := false
	preferred := 0
	if affinity == 0 {
		preferred = 1
	}
	for _, r := range rows {
		for end := 0; end < 2; end++ {
			if r[end] == offset {
				chosen = documentEdge(source, r, end)
				found = true
				if end == preferred {
					return chosen, nil
				}
			}
		}
	}
	if len(rows) > 0 && !found {
		return [3]uint32{}, errors.New("invalid Unicode or caret boundary")
	}
	return chosen, nil
}
