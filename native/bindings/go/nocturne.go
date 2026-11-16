// Package native owns a direct C context. It never starts Node or owns a terminal.
package native

/*
#cgo CFLAGS: -I${SRCDIR}/../../include
#cgo linux LDFLAGS: -L${SRCDIR}/../../dist -lnocturne_native -Wl,-rpath,${SRCDIR}/../../dist
#cgo darwin LDFLAGS: -L${SRCDIR}/../../dist -lnocturne_native -Wl,-rpath,${SRCDIR}/../../dist
#include <stdlib.h>
#include "nocturne_native.h"
// A named wrapper returns NULL to Go on exhaustion; cgo's special C.malloc
// spelling aborts instead of returning an allocation failure.
static void *nrOwnedMalloc(size_t size) { return malloc(size); }
*/
import "C"
import (
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"hash/crc32"
	"math"
	"sync"
	"unicode/utf8"
	"unsafe"
)

// Scene serializes the current native context. Close releases its allocation.
type Scene struct {
	mu           sync.Mutex
	context      *C.NrContext
	renderMemory unsafe.Pointer
	promptMemory unsafe.Pointer
	modelMemory  unsafe.Pointer
	modalMemory unsafe.Pointer
}

// Frame owns canonical little-endian glyph, foreground, background and ID bytes.
type Frame struct {
	Width  uint32
	Height uint32
	Bytes  []byte
}
type CharacterCellInfo struct {
	Glyph, Foreground, Background, ID, Index uint32
	Role, State, Path                        string
}

// InspectCharacterCell copies current render metadata and never draws implicitly.
func (s *Scene) InspectCharacterCell(x, y int32) (CharacterCellInfo, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return CharacterCellInfo{}, errors.New("closed")
	}
	var out C.NrCharacterCellInfo
	status := C.nrInspectCharacterCell(s.context, C.int32_t(x), C.int32_t(y), &out, C.uint32_t(C.sizeof_NrCharacterCellInfo))
	if status == -2 {
		return CharacterCellInfo{}, errors.New("render required before cell inspection")
	}
	if status != 0 {
		return CharacterCellInfo{}, errors.New("cell inspection rejected")
	}
	return CharacterCellInfo{uint32(out.cell.glyph), uint32(out.cell.foreground), uint32(out.cell.background), uint32(out.cell.id), uint32(out.index), C.GoString(&out.role[0]), C.GoString(&out.state[0]), C.GoString(&out.path[0])}, nil
}

// New creates a context with an explicit uint32 seed and no device access.
func New(seed uint32) (*Scene, error) {
	size := C.nrContextSize()
	memory := C.nrOwnedMalloc(C.size_t(size))
	if memory == nil {
		return nil, errors.New("allocation failed")
	}
	if C.nrInit(memory, size, C.uint32_t(seed)) != 0 {
		C.free(memory)
		return nil, errors.New("native init failed")
	}
	return &Scene{context: (*C.NrContext)(memory)}, nil
}

// Close releases the native context. It is safe to call repeatedly.
func (s *Scene) Close() {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context != nil {
		C.free(s.renderMemory)
		s.renderMemory = nil
		C.free(s.modalMemory)
		s.modalMemory=nil
		C.free(s.modelMemory)
		s.modelMemory = nil
		C.free(s.promptMemory)
		s.promptMemory = nil
		C.free(unsafe.Pointer(s.context))
		s.context = nil
	}
}

// CommandRaw applies bounded UTF-8 JSON transactionally. Return 1 means catch-up remains.
func (s *Scene) CommandRaw(raw []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return 0, errors.New("closed")
	}
	if len(raw) == 0 || uint64(len(raw)) > uint64(^uint32(0)) {
		return 0, errors.New("command size")
	}
	code := int(C.nrCommand(s.context, (*C.char)(unsafe.Pointer(&raw[0])), C.uint32_t(len(raw))))
	for code < 0 {
		message := C.GoString(C.nrError(s.context))
		if message == "Prompt storage required" {
			if e := s.ensurePromptMemory(); e != nil {
				return 0, e
			}
		} else if message == "Modal storage required" {
            if e := s.ensureModalMemory(); e != nil {return 0,e}
        } else if message == "Viewport render memory required" {
			before := C.nrRenderMemoryCapacity(s.context)
			if e := s.ensureRenderMemory(); e != nil {
				return 0, e
			}
			if C.nrRenderMemoryCapacity(s.context) <= before {
				return 0, errors.New("viewport storage request made no progress")
			}
		} else {
			break
		}
		code = int(C.nrCommand(s.context, (*C.char)(unsafe.Pointer(&raw[0])), C.uint32_t(len(raw))))
	}
	if code < 0 {
		return code, errors.New(C.GoString(C.nrError(s.context)))
	}
	return code, nil
}

// Command validates JSON serialization and applies one current-contract operation.
func (s *Scene) Command(value any) (int, error) {
	b, e := json.Marshal(value)
	if e != nil {
		return 0, e
	}
	return s.CommandRaw(b)
}

// AdvanceTo synchronously catches up; interactive hosts can issue bounded Command batches.
func (s *Scene) AdvanceTo(us uint64) error {
	for {
		n, e := s.Command(map[string]any{"op": "time", "timeUs": us})
		if e != nil {
			return e
		}
		if n != 1 {
			return nil
		}
	}
}

// ensurePromptMemory preserves the old allocation until native rebinding succeeds.
func (s *Scene) ensurePromptMemory() error {
	required := C.nrPromptMemorySize(s.context)
	if required <= C.nrPromptMemoryCapacity(s.context) {
		return errors.New("prompt storage request made no progress")
	}
	if uint64(required) > uint64(^uintptr(0)) {
		return errors.New("prompt exceeds address space")
	}
	memory := C.nrOwnedMalloc(C.size_t(required))
	if memory == nil {
		return errors.New("prompt allocation failed")
	}
	if C.nrSetPromptMemory(s.context, memory, required) != 0 {
		C.free(memory)
		return errors.New("prompt storage rejected")
	}
	C.free(s.promptMemory)
	s.promptMemory = memory
	return nil
}

// Render samples a pure owned frame without advancing state.
func (s *Scene) ensureRenderMemory() error {
	required := C.nrRenderMemorySize(s.context)
	if required <= C.nrRenderMemoryCapacity(s.context) {
		return nil
	}
	if uint64(required) > uint64(^uintptr(0)) {
		return errors.New("viewport exceeds address space")
	}
	memory := C.nrOwnedMalloc(C.size_t(required))
	if memory == nil {
		return errors.New("viewport allocation failed")
	}
	if C.nrSetRenderMemory(s.context, memory, required) != 0 {
		C.free(memory)
		return errors.New("viewport render memory rejected")
	}
	C.free(s.renderMemory)
	s.renderMemory = memory
	return nil
}

// Render samples a pure owned frame without advancing state.
func (s *Scene) Render() (Frame, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return Frame{}, errors.New("closed")
	}
	if e := s.ensureRenderMemory(); e != nil {
		return Frame{}, e
	}
	n := C.nrRender(s.context)
	if n == 0 {
		return Frame{}, errors.New("render failed")
	}
	count := uint64(n) * 16
	if count > uint64(^uint(0)>>1) {
		return Frame{}, errors.New("frame exceeds Go slice address space")
	}
	bytes := append([]byte(nil), unsafe.Slice((*byte)(unsafe.Pointer(C.nrCells(s.context))), int(count))...)
	return Frame{uint32(C.nrWidth(s.context)), uint32(C.nrHeight(s.context)), bytes}, nil
}

// Info returns a copied JSON metadata record, including complete authoritative text.
func (s *Scene) Info() ([]byte, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	return []byte(C.GoString(C.nrInfo(s.context))), nil
}

// InfoComplete recovers complete JSON on demand, not on animation frames.
// The context lock spans all pages. Output grows to the native u32 size and
// available Go slice address space. CRC32 checks
// accidental consistency, not authenticity. Info retains its old capacity policy.
func (s *Scene) InfoComplete() ([]byte, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	page := make([]byte, 65536)
	var data []byte
	var offset, total, checksum uint32
	for {
		var words [4]C.uint32_t
		status := int(C.nrInfoPage(s.context, C.uint32_t(offset), unsafe.Pointer(&page[0]), 65536, &words[0], 4))
		if status != 0 && status != 1 {
			return nil, errors.New("metadata page rejected")
		}
		size, written, next, token := uint32(words[0]), uint32(words[1]), uint32(words[2]), uint32(words[3])
		if uint64(size) > uint64(^uint(0)>>1) {
			return nil, errors.New("complete metadata exceeds Go slice address space")
		}
		if size < offset || written != min(uint32(65536), size-offset) || next != offset+written || (status == 1) != (next < size) {
			return nil, errors.New("invalid metadata page progress")
		}
		if data == nil {
			total = size
			checksum = token
			data = make([]byte, 0, int(size))
		} else if total != size || checksum != token {
			return nil, errors.New("metadata changed during recovery")
		}
		data = append(data, page[:written]...)
		offset = next
		if status == 0 {
			if len(data) != int(total) || crc32.ChecksumIEEE(data) != checksum {
				return nil, errors.New("metadata recovery checksum mismatch")
			}
			return data, nil
		}
	}
}

// Snapshot owns a compatible-schema, pointer-free context image with checksum.
func (s *Scene) Snapshot() ([]byte, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	size := int(C.nrSnapshotSizeFor(s.context))
	if size < 24 {
		return nil, errors.New("snapshot size unavailable")
	}
	b := make([]byte, size)
	if C.nrSave(s.context, unsafe.Pointer(&b[0]), C.uint32_t(size)) != 0 {
		return nil, errors.New("snapshot failed")
	}
	return b, nil
}

// Restore rejects incompatible/corrupt snapshots without changing authoritative state.
func (s *Scene) Restore(b []byte) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return errors.New("closed")
	}
	if len(b) < 24 || uint64(len(b)) > uint64(^uint32(0)) || uint64(binary.LittleEndian.Uint32(b[16:20])) != uint64(len(b)-24) {
		return fmt.Errorf("snapshot size %d", len(b))
	}
	for {
		if C.nrLoad(s.context, unsafe.Pointer(&b[0]), C.uint32_t(len(b))) == 0 {
			break
		}
		var e error
		switch C.GoString(C.nrError(s.context)) {
		case "Prompt storage required":
			e = s.ensurePromptMemory()
		case "Modal storage required":
            e = s.ensureModalMemory()
        case "Model storage required":
			e = s.ensureModelMemory()
		default:
			return errors.New("snapshot rejected")
		}
		if e != nil {
			return e
		}
	}
	return nil
}

// Catalogue returns the current implementation descriptors; visual acceptance is separate.
func (s *Scene) Catalogue() ([]byte, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	return []byte(C.GoString(C.nrCatalogue())), nil
}

// Particles copies active particle identity, state, position, velocity and lifetime words.
func (s *Scene) Particles() ([][12]int32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	var out [][12]int32
	for i := 0; i < 2048; i++ {
		var p [12]C.int32_t
		if C.nrParticle(s.context, C.uint32_t(i), &p[0], 12) > 0 {
			var copy [12]int32
			for j := range p {
				copy[j] = int32(p[j])
			}
			out = append(out, copy)
		}
	}
	return out, nil
}

// Oklch converts normalized lightness/chroma and hue in degrees using the current native converter.
func Oklch(l, c, h float64) (uint32, error) {
	if math.IsNaN(l) || math.IsNaN(c) || math.IsNaN(h) || math.IsInf(l, 0) || math.IsInf(c, 0) || math.IsInf(h, 0) || l < 0 || l > 1 || c < 0 || c > .5 || h < -36000 || h > 36000 {
		return 0, errors.New("color bounds")
	}
	out := uint32(C.nrOklch(C.int32_t(math.Round(l*1e6)), C.int32_t(math.Round(c*1e6)), C.int32_t(math.Round(h*1000))))
	if out == 0xffffffff {
		return 0, errors.New("color rejected")
	}
	return out, nil
}

// Composite performs pure encoded-RGB blending and independent Porter-Duff coverage.
func Composite(base, source, baseAlpha, sourceAlpha, blend, operation, seed uint32) ([2]uint32, error) {
	var out [2]C.uint32_t
	if C.nrComposite(C.uint32_t(base), C.uint32_t(source), C.uint32_t(baseAlpha), C.uint32_t(sourceAlpha), C.uint32_t(blend), C.uint32_t(operation), C.uint32_t(seed), &out[0]) < 0 {
		return [2]uint32{}, errors.New("composition rejected")
	}
	return [2]uint32{uint32(out[0]), uint32(out[1])}, nil
}

// CompositeInSpace uses 0=sRGB, 1=linear sRGB, 2=OKLab, 3=OKLCh alpha mixing.
func CompositeInSpace(base, source, baseAlpha, sourceAlpha, blend, operation, seed, space uint32) ([2]uint32, error) {
	var out [2]C.uint32_t
	if C.nrCompositeInSpace(C.uint32_t(base), C.uint32_t(source), C.uint32_t(baseAlpha), C.uint32_t(sourceAlpha), C.uint32_t(blend), C.uint32_t(operation), C.uint32_t(seed), C.uint32_t(space), &out[0]) < 0 {
		return [2]uint32{}, errors.New("composition rejected")
	}
	return [2]uint32{uint32(out[0]), uint32(out[1])}, nil
}

// TextSample copies display/source scalars, identity, XY Q16, alpha, hue and settled.
func (s *Scene) TextSample(id, index uint32) ([8]int32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var out [8]int32
	if s.context == nil {
		return out, errors.New("closed")
	}
	if C.nrTextSample(s.context, C.uint32_t(id), C.uint32_t(index), (*C.int32_t)(unsafe.Pointer(&out[0])), 8) != 0 {
		return out, errors.New("text run or index not found")
	}
	return out, nil
}

// TextClusterSample returns persistent ID bits, source span and native anchor pose.
func (s *Scene) TextClusterSample(id, index uint32) ([8]int32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var out [8]int32
	if s.context == nil {
		return out, errors.New("closed")
	}
	if C.nrTextClusterSample(s.context, C.uint32_t(id), C.uint32_t(index), (*C.int32_t)(unsafe.Pointer(&out[0])), 8) != 0 {
		return out, errors.New("text cluster not found")
	}
	return out, nil
}

// TextTrailSample returns owned source identity bits, glyph, ordinal, XY Q16, alpha, hue, settled.
func (s *Scene) TextTrailSample(id, index, trail uint32) ([8]int32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var out [8]int32
	if s.context == nil {
		return out, errors.New("closed")
	}
	if C.nrTextTrailSample(s.context, C.uint32_t(id), C.uint32_t(index), C.uint32_t(trail), (*C.int32_t)(unsafe.Pointer(&out[0])), 8) != 0 {
		return out, errors.New("text trail not found")
	}
	return out, nil
}

// WindowSample uses integer millionths for UV/visibility; output is XYZ Q16, alpha, mask.
func (s *Scene) WindowSample(id, u, v, visibility uint32) ([5]int32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var out [5]int32
	if s.context == nil {
		return out, errors.New("closed")
	}
	if C.nrWindowSample(s.context, C.uint32_t(id), C.uint32_t(u), C.uint32_t(v), C.uint32_t(visibility), (*C.int32_t)(unsafe.Pointer(&out[0])), 5) != 0 {
		return out, errors.New("window sample bounds or unknown identity")
	}
	return out, nil
}

// Batch atomically commits up to 64 supported scene edits.
func (s *Scene) Batch(commands []any) error {
	_, err := s.Command(map[string]any{"op": "batch", "commands": commands})
	return err
}

// Schedule queues one scene edit at an explicit simulation time.
func (s *Scene) Schedule(id uint32, atUs uint64, command any) error {
	_, err := s.Command(map[string]any{"op": "schedule", "id": id, "atUs": atUs, "command": command})
	return err
}

// ParticleMotions returns copied stable IDs, XYZ degrees and XYZ degrees/second.
func (s *Scene) ParticleMotions() ([][7]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	out := make([][7]float64, 0)
	for i := 0; i < 2048; i++ {
		var values [6]C.double
		var p [12]C.int32_t
		if C.nrParticleMotion(s.context, C.uint32_t(i), &values[0], 6) > 0 {
			C.nrParticle(s.context, C.uint32_t(i), &p[0], 12)
			row := [7]float64{float64(uint32(p[0]))}
			for j := range values {
				row[j+1] = float64(values[j])
			}
			out = append(out, row)
		}
	}
	return out, nil
}

// GraphemeBoundaries returns Unicode 17 boundaries in scalar offsets, owned by caller.
// GraphemeWidths returns owned start/end scalar offsets and columns under nr-grapheme-cell-width-v1.
func (s *Scene) GraphemeWidths(text string, ambiguous uint32) ([][3]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	if ambiguous != 1 && ambiguous != 2 {
		return nil, errors.New("ambiguous width must be 1 or 2")
	}
	if !utf8.ValidString(text) || utf8.RuneCountInString(text) > 2048 {
		return nil, errors.New("invalid Unicode or capacity")
	}
	runes := []rune(text)
	values := make([]C.uint32_t, len(runes))
	for i, r := range runes {
		values[i] = C.uint32_t(r)
	}
	var input *C.uint32_t
	if len(values) > 0 {
		input = &values[0]
	}
	output := make([]C.uint32_t, len(values)*3+1)
	count := C.nrGraphemeWidths(input, C.uint32_t(len(values)), C.uint32_t(ambiguous), &output[0], C.uint32_t(len(values)))
	if count < 0 {
		return nil, errors.New("invalid Unicode scalar")
	}
	owned := make([][3]uint32, int(count))
	for i := range owned {
		for j := 0; j < 3; j++ {
			owned[i][j] = uint32(output[i*3+j])
		}
	}
	return owned, nil
}

// GraphemeLayout returns owned start/end scalar offsets, column, row and width.
func (s *Scene) GraphemeLayout(text string, columns, ambiguous uint32) ([][5]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	if columns == 0 {
		return nil, errors.New("positive columns required")
	}
	if ambiguous != 1 && ambiguous != 2 {
		return nil, errors.New("ambiguous width must be 1 or 2")
	}
	if !utf8.ValidString(text) || utf8.RuneCountInString(text) > 2048 {
		return nil, errors.New("invalid Unicode or capacity")
	}
	runes := []rune(text)
	values := make([]C.uint32_t, len(runes))
	for i, r := range runes {
		values[i] = C.uint32_t(r)
	}
	var input *C.uint32_t
	if len(values) > 0 {
		input = &values[0]
	}
	output := make([]C.uint32_t, len(values)*5+1)
	count := C.nrGraphemeLayout(input, C.uint32_t(len(values)), C.uint32_t(ambiguous), C.uint32_t(columns), &output[0], C.uint32_t(len(values)))
	if count < 0 {
		return nil, errors.New("invalid Unicode scalar")
	}
	owned := make([][5]uint32, int(count))
	for i := range owned {
		for j := 0; j < 5; j++ {
			owned[i][j] = uint32(output[i*5+j])
		}
	}
	return owned, nil
}

// LineBreaks returns Unicode 17 line opportunities in owned scalar offsets.
func (s *Scene) LineBreaks(text string) ([]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	if !utf8.ValidString(text) || utf8.RuneCountInString(text) > 2048 {
		return nil, errors.New("invalid Unicode or capacity")
	}
	runes := []rune(text)
	values := make([]C.uint32_t, len(runes))
	for i, r := range runes {
		values[i] = C.uint32_t(r)
	}
	var input *C.uint32_t
	if len(values) > 0 {
		input = &values[0]
	}
	output := make([]C.uint32_t, len(values)+1)
	count := C.nrLineBreaks(input, C.uint32_t(len(values)), &output[0], C.uint32_t(len(output)))
	if count < 0 {
		return nil, errors.New("invalid Unicode scalar")
	}
	owned := make([]uint32, int(count))
	for i := range owned {
		owned[i] = uint32(output[i])
	}
	return owned, nil
}

// LineBreakDetails returns owned scalar offset and mandatory (0 or 1) rows.
func (s *Scene) LineBreakDetails(text string) ([][2]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	if !utf8.ValidString(text) || utf8.RuneCountInString(text) > 2048 {
		return nil, errors.New("invalid Unicode or capacity")
	}
	runes := []rune(text)
	values := make([]C.uint32_t, len(runes))
	for i, r := range runes {
		values[i] = C.uint32_t(r)
	}
	var input *C.uint32_t
	if len(values) > 0 {
		input = &values[0]
	}
	output := make([]C.uint32_t, 2*(len(values)+1))
	count := C.nrLineBreakDetails(input, C.uint32_t(len(values)), &output[0], C.uint32_t(len(values)+1))
	if count < 0 {
		return nil, errors.New("invalid Unicode scalar")
	}
	owned := make([][2]uint32, int(count))
	for i := range owned {
		owned[i] = [2]uint32{uint32(output[2*i]), uint32(output[2*i+1])}
	}
	return owned, nil
}

func (s *Scene) GraphemeBoundaries(text string) ([]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	if !utf8.ValidString(text) || utf8.RuneCountInString(text) > 2048 {
		return nil, errors.New("invalid Unicode or capacity")
	}
	runes := []rune(text)
	values := make([]C.uint32_t, len(runes))
	for i, r := range runes {
		values[i] = C.uint32_t(r)
	}
	var input *C.uint32_t
	if len(values) > 0 {
		input = &values[0]
	}
	output := make([]C.uint32_t, len(values)+1)
	count := C.nrGraphemeBreaks(input, C.uint32_t(len(values)), &output[0], C.uint32_t(len(output)))
	if count < 0 {
		return nil, errors.New("invalid Unicode scalar")
	}
	owned := make([]uint32, int(count))
	for i := range owned {
		owned[i] = uint32(output[i])
	}
	return owned, nil
}

// GraphemeHit maps a logical pointer to a complete scalar-source boundary.
func (s *Scene) GraphemeHit(text string, columns, column, row, ambiguous uint32) (uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return 0, errors.New("closed")
	}
	if columns == 0 || (ambiguous != 1 && ambiguous != 2) {
		return 0, errors.New("invalid layout policy")
	}
	if !utf8.ValidString(text) || utf8.RuneCountInString(text) > 2048 {
		return 0, errors.New("invalid Unicode or capacity")
	}
	runes := []rune(text)
	values := make([]C.uint32_t, len(runes))
	for i, r := range runes {
		values[i] = C.uint32_t(r)
	}
	var input *C.uint32_t
	if len(values) > 0 {
		input = &values[0]
	}
	result := C.nrGraphemeHit(input, C.uint32_t(len(values)), C.uint32_t(ambiguous), C.uint32_t(columns), C.uint32_t(column), C.uint32_t(row))
	if result < 0 {
		return 0, errors.New("invalid Unicode scalar")
	}
	return uint32(result), nil
}

// SelectedText copies selected scalar source; empty means absent or not owned.
func (s *Scene) SelectedText() (string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return "", errors.New("closed")
	}
	count := C.nrPromptSelection(s.context, nil, 0)
	if count == 0 {
		return "", nil
	}
	if count < 0 {
		return "", errors.New("invalid selection export")
	}
	output := make([]C.uint32_t, int(count))
	if C.nrPromptSelection(s.context, &output[0], C.uint32_t(count)) != count {
		return "", errors.New("selection changed during read")
	}
	if count < 0 {
		return "", errors.New("invalid selection export")
	}
	runes := make([]rune, int(count))
	for i := range runes {
		runes[i] = rune(output[i])
	}
	return string(runes), nil
}

// TextRunClusters returns owned identity, source span and run generation rows.
func (s *Scene) TextRunClusters(kind, id uint32) ([][4]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	n := C.nrTextRunClusters(s.context, C.uint32_t(kind), C.uint32_t(id), nil, 0)
	if n < 0 {
		return nil, errors.New("invalid text run query")
	}
	if n == 0 {
		return [][4]uint32{}, nil
	}
	out := make([]C.uint32_t, int(n)*4)
	if C.nrTextRunClusters(s.context, C.uint32_t(kind), C.uint32_t(id), &out[0], C.uint32_t(n)) != n {
		return nil, errors.New("text run changed during read")
	}
	if n < 0 {
		return nil, errors.New("missing or invalid text run")
	}
	rows := make([][4]uint32, int(n))
	for i := range rows {
		for j := range rows[i] {
			rows[i][j] = uint32(out[i*4+j])
		}
	}
	return rows, nil
}

// TextRunSource copies a context-owned prompt/text/window source by (kind,id).
func (s *Scene) TextRunSource(kind, id uint32) (string, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return "", errors.New("closed")
	}
	n := C.nrTextRunSource(s.context, C.uint32_t(kind), C.uint32_t(id), nil, 0)
	if n < 0 {
		return "", errors.New("missing or invalid text run")
	}
	if n == 0 {
		return "", nil
	}
	out := make([]C.uint32_t, int(n))
	written := C.nrTextRunSource(s.context, C.uint32_t(kind), C.uint32_t(id), &out[0], C.uint32_t(n))
	if written != n {
		return "", errors.New("text source changed during read")
	}
	runes := make([]rune, int(n))
	for i := range runes {
		runes[i] = rune(out[i])
	}
	return string(runes), nil
}

// TextRunLayout returns copied [id,start,end,column,row,width,kind] rows.
func (s *Scene) TextRunLayout(kind, id, columns, ambiguous uint32) ([][7]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	n := C.nrTextRunLayout(s.context, C.uint32_t(kind), C.uint32_t(id), C.uint32_t(ambiguous), C.uint32_t(columns), nil, 0)
	if n < 0 {
		return nil, errors.New("invalid text run query")
	}
	if n == 0 {
		return [][7]uint32{}, nil
	}
	out := make([]C.uint32_t, int(n)*7)
	if C.nrTextRunLayout(s.context, C.uint32_t(kind), C.uint32_t(id), C.uint32_t(ambiguous), C.uint32_t(columns), &out[0], C.uint32_t(n)) != n {
		return nil, errors.New("text run changed during read")
	}
	if n < 0 {
		return nil, errors.New("missing run or invalid layout policy")
	}
	rows := make([][7]uint32, int(n))
	for i := range rows {
		for j := range rows[i] {
			rows[i][j] = uint32(out[i*7+j])
		}
	}
	return rows, nil
}

// TextRunHit maps local logical coordinates to a whole source cluster boundary.
func (s *Scene) TextRunHit(kind, id, columns, column, row, ambiguous uint32) (uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return 0, errors.New("closed")
	}
	n := C.nrTextRunHit(s.context, C.uint32_t(kind), C.uint32_t(id), C.uint32_t(ambiguous), C.uint32_t(columns), C.uint32_t(column), C.uint32_t(row))
	if n < 0 {
		return 0, errors.New("missing run or invalid layout policy")
	}
	return uint32(n), nil
}

// TextRunClip returns whole source rows plus explicit visible column intersections.
func (s *Scene) TextRunClip(kind, id, columns, x, y, width, height, ambiguous uint32) ([][9]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	n := C.nrTextRunClip(s.context, C.uint32_t(kind), C.uint32_t(id), C.uint32_t(ambiguous), C.uint32_t(columns), C.uint32_t(x), C.uint32_t(y), C.uint32_t(width), C.uint32_t(height), nil, 0)
	if n < 0 {
		return nil, errors.New("invalid text run query")
	}
	if n == 0 {
		return [][9]uint32{}, nil
	}
	out := make([]C.uint32_t, int(n)*9)
	if C.nrTextRunClip(s.context, C.uint32_t(kind), C.uint32_t(id), C.uint32_t(ambiguous), C.uint32_t(columns), C.uint32_t(x), C.uint32_t(y), C.uint32_t(width), C.uint32_t(height), &out[0], C.uint32_t(n)) != n {
		return nil, errors.New("text run changed during read")
	}
	if n < 0 {
		return nil, errors.New("missing run or invalid layout policy")
	}
	rows := make([][9]uint32, int(n))
	for i := range rows {
		for j := range rows[i] {
			rows[i][j] = uint32(out[i*9+j])
		}
	}
	return rows, nil
}

// BidiVisual copies scalar visual order with source indices, classes, levels and mirrors.
func (s *Scene) BidiVisual(text string, direction uint32) ([][4]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	if direction > 2 || !utf8.ValidString(text) || utf8.RuneCountInString(text) > 2048 {
		return nil, errors.New("invalid Unicode, capacity or direction")
	}
	runes := []rune(text)
	values := make([]C.uint32_t, len(runes))
	for i, r := range runes {
		values[i] = C.uint32_t(r)
	}
	var input *C.uint32_t
	if len(values) > 0 {
		input = &values[0]
	}
	out := make([]C.uint32_t, 2048*4)
	n := C.nrBidiVisual(input, C.uint32_t(len(values)), C.uint32_t(direction), &out[0], 2048)
	if n < 0 {
		return nil, errors.New("invalid Unicode scalar")
	}
	rows := make([][4]uint32, int(n))
	for i := range rows {
		for j := range rows[i] {
			rows[i][j] = uint32(out[i*4+j])
		}
	}
	return rows, nil
}

// BidiLayout reorders whole Unicode clusters per logical wrapped cell line.
func (s *Scene) BidiLayout(text string, columns, direction, ambiguous uint32) ([][7]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	if direction > 2 || columns == 0 || (ambiguous != 1 && ambiguous != 2) || !utf8.ValidString(text) || utf8.RuneCountInString(text) > 2048 {
		return nil, errors.New("invalid bidi layout policy, Unicode or capacity")
	}
	runes := []rune(text)
	values := make([]C.uint32_t, len(runes))
	for i, r := range runes {
		values[i] = C.uint32_t(r)
	}
	var input *C.uint32_t
	if len(values) > 0 {
		input = &values[0]
	}
	out := make([]C.uint32_t, 2048*7)
	n := C.nrBidiClusterLayout(input, C.uint32_t(len(values)), C.uint32_t(ambiguous), C.uint32_t(columns), C.uint32_t(direction), &out[0], 2048)
	if n < 0 {
		return nil, errors.New("invalid Unicode scalar")
	}
	rows := make([][7]uint32, int(n))
	for i := range rows {
		for j := range rows[i] {
			rows[i][j] = uint32(out[i*7+j])
		}
	}
	return rows, nil
}

func bidiMappingScalars(text string, columns, direction, ambiguous uint32) ([]C.uint32_t, uint32, error) {
	if direction > 2 || columns == 0 || (ambiguous != 1 && ambiguous != 2) || !utf8.ValidString(text) || utf8.RuneCountInString(text) > 2048 {
		return nil, 0, errors.New("invalid bidi mapping input")
	}
	runes := []rune(text)
	size := len(runes)
	if size == 0 {
		size = 1
	}
	values := make([]C.uint32_t, size)
	for i, r := range runes {
		values[i] = C.uint32_t(r)
	}
	return values, uint32(len(runes)), nil
}

// BidiHit maps visual cell coordinates to a whole logical source boundary.
func (s *Scene) BidiHit(text string, columns, column, row, direction, ambiguous uint32) (uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return 0, errors.New("closed")
	}
	values, count, e := bidiMappingScalars(text, columns, direction, ambiguous)
	if e != nil {
		return 0, e
	}
	n := C.nrBidiClusterHit(&values[0], C.uint32_t(count), C.uint32_t(ambiguous), C.uint32_t(columns), C.uint32_t(direction), C.uint32_t(column), C.uint32_t(row))
	if n < 0 {
		return 0, errors.New("invalid bidi hit input")
	}
	return uint32(n), nil
}

// BidiCaret copies [column,row,level]; affinity 0 precedes, 1 follows the offset.
func (s *Scene) BidiCaret(text string, columns, offset, affinity, direction, ambiguous uint32) ([3]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return [3]uint32{}, errors.New("closed")
	}
	values, count, e := bidiMappingScalars(text, columns, direction, ambiguous)
	if e != nil {
		return [3]uint32{}, e
	}
	out := make([]C.uint32_t, 3)
	n := C.nrBidiCaret(&values[0], C.uint32_t(count), C.uint32_t(ambiguous), C.uint32_t(columns), C.uint32_t(direction), C.uint32_t(offset), C.uint32_t(affinity), &out[0], 3)
	if n < 0 {
		return [3]uint32{}, errors.New("invalid bidi caret input")
	}
	return [3]uint32{uint32(out[0]), uint32(out[1]), uint32(out[2])}, nil
}

// WaveSample samples the shared native analytic field in world units and seconds.
func (s *Scene) WaveSample(waves [][5]float64, x, z, seconds float64) ([6]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var result [6]float64
	if s.context == nil || len(waves) > 32 {
		return result, errors.New("closed or wave capacity")
	}
	values := make([]C.double, len(waves)*5)
	for i, w := range waves {
		for j, v := range w {
			values[i*5+j] = C.double(v)
		}
	}
	var input *C.double
	if len(values) > 0 {
		input = &values[0]
	}
	var out [6]C.double
	if C.nrWaveSample(input, C.uint32_t(len(waves)), C.double(x), C.double(z), C.double(seconds), &out[0], 6) != 1 {
		return result, errors.New("invalid wave field")
	}
	for i, v := range out {
		result[i] = float64(v)
	}
	return result, nil
}

func (s *Scene) SurfaceWaveSample(id uint32, x, z float64) ([6]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var result [6]float64
	if s.context == nil {
		return result, errors.New("closed")
	}
	var out [6]C.double
	if C.nrSurfaceWaveSample(s.context, C.uint32_t(id), C.double(x), C.double(z), &out[0], 6) != 1 {
		return result, errors.New("invalid surface wave sample")
	}
	for i, v := range out {
		result[i] = float64(v)
	}
	return result, nil
}

// FloatBody returns owned position/velocity/normal, immersion, buoyant force and mass.
// An absent body returns nil without error.
func (s *Scene) FloatBody(id uint32) ([]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	var out [12]C.double
	result := C.nrFloatBody(s.context, C.uint32_t(id), &out[0], 12)
	if result < 0 {
		return nil, errors.New("invalid float body query")
	}
	if result == 0 {
		return nil, nil
	}
	values := make([]float64, 12)
	for i, v := range out {
		values[i] = float64(v)
	}
	return values, nil
}

// SurfaceFoam returns owned triangle/intensity/generated/decayed/saturated rows.
func (s *Scene) SurfaceFoam(id uint32) ([][5]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	out := make([]C.double, 256*5)
	count := C.nrSurfaceFoam(s.context, C.uint32_t(id), &out[0], 256)
	if count < 0 {
		return nil, errors.New("invalid surface foam query")
	}
	rows := make([][5]float64, int(count))
	for i := range rows {
		for j := range rows[i] {
			rows[i][j] = float64(out[i*5+j])
		}
	}
	return rows, nil
}

// FlowThickness returns owned flux, depth, area, width, speed, maximum depth.
func (s *Scene) FlowThickness(id uint32) ([]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	out := make([]C.double, 6)
	result := C.nrFlowThickness(s.context, C.uint32_t(id), &out[0], 6)
	if result < 0 {
		return nil, errors.New("invalid flow thickness query")
	}
	if result == 0 {
		return nil, nil
	}
	owned := make([]float64, 6)
	for i := range owned {
		owned[i] = float64(out[i])
	}
	return owned, nil
}

// SurfaceTriangles returns owned current geometry: ordinal, XYZ vertices, RGB, alpha.
func (s *Scene) SurfaceTriangles(id uint32) ([][12]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	out := make([]C.double, 256*12)
	count := C.nrSurfaceTriangles(s.context, C.uint32_t(id), &out[0], 256)
	if count < 0 {
		return nil, errors.New("invalid surface geometry query")
	}
	rows := make([][12]float64, int(count))
	for i := range rows {
		for j := range rows[i] {
			rows[i][j] = float64(out[i*12+j])
		}
	}
	return rows, nil
}

// AreaGeometry returns owned origin, size, effective clip and content bounds.
func (s *Scene) PromptLayout() ([][8]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	n := int(C.nrPromptLayout(s.context, nil, 0))
	if n < 0 {
		return nil, errors.New("invalid prompt layout")
	}
	rows := make([][8]float64, n)
	if n > 0 && int(C.nrPromptLayout(s.context, (*C.double)(unsafe.Pointer(&rows[0][0])), C.uint32_t(n))) != n {
		return nil, errors.New("invalid prompt layout")
	}
	return rows, nil
}

func (s *Scene) AreaGeometry(id uint32) (*[12]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	var out [12]C.double
	result := C.nrAreaGeometry(s.context, C.uint32_t(id), &out[0], 12)
	if result < 0 {
		return nil, errors.New("invalid area geometry")
	}
	if result == 0 {
		return nil, nil
	}
	row := new([12]float64)
	for i := range row {
		row[i] = float64(out[i])
	}
	return row, nil
}

// FieldSample returns an owned intensity/RGB/global-center row, or nil if absent.
func (s *Scene) FieldSample(id uint32, x, y float64) (*[4]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	var out [4]C.double
	result := C.nrFieldSample(s.context, C.uint32_t(id), C.double(x), C.double(y), &out[0], 4)
	if result < 0 {
		return nil, errors.New("invalid field sample")
	}
	if result == 0 {
		return nil, nil
	}
	row := new([4]float64)
	for i := range row {
		row[i] = float64(out[i])
	}
	return row, nil
}

// WaterSample returns an owned eight-double cell ledger, or nil if unconfigured.
func (s *Scene) WaterSample(index uint32) (*[8]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	var out [8]C.double
	result := C.nrWaterSample(s.context, C.uint32_t(index), &out[0], 8)
	if result < 0 {
		return nil, errors.New("invalid water sample")
	}
	if result == 0 {
		return nil, nil
	}
	row := new([8]float64)
	for i := range row {
		row[i] = float64(out[i])
	}
	return row, nil
}

// ThermalSample returns an owned ten-double thermal ledger, or nil if unconfigured.
func (s *Scene) ThermalSample(index uint32) (*[10]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	var out [10]C.double
	result := C.nrThermalSample(s.context, C.uint32_t(index), &out[0], 10)
	if result < 0 {
		return nil, errors.New("invalid thermal sample")
	}
	if result == 0 {
		return nil, nil
	}
	row := new([10]float64)
	for i := range row {
		row[i] = float64(out[i])
	}
	return row, nil
}

// SurfaceFoamTransport returns owned foam rows with incoming/outgoing inventory.
func (s *Scene) SurfaceFoamTransport(id uint32) ([][7]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	out := make([]C.double, 256*7)
	count := C.nrSurfaceFoamTransport(s.context, C.uint32_t(id), &out[0], 256)
	if count < 0 {
		return nil, errors.New("invalid surface foam query")
	}
	rows := make([][7]float64, int(count))
	for i := range rows {
		for j := range rows[i] {
			rows[i][j] = float64(out[i*7+j])
		}
	}
	return rows, nil
}

// PathSample returns XYZ, travel tangent XYZ, total length and resolved distance.
// Mode 0 clamps, 1 loops and 2 reverses travel at the endpoints.
func (s *Scene) PathSample(points [][3]float64, distance float64, closed bool, mode uint32) ([8]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var result [8]float64
	if s.context == nil {
		return result, errors.New("NativeScene is closed")
	}
	if len(points) < 2 || len(points) > 129 || mode > 2 {
		return result, errors.New("Invalid path shape or mode")
	}
	flag := C.int(0)
	if closed {
		flag = 1
	}
	var out [8]C.double
	if C.nrPathSample((*C.double)(unsafe.Pointer(&points[0][0])), C.uint32_t(len(points)), flag, C.int(mode), C.double(distance), &out[0], 8) != 1 {
		return result, errors.New("Invalid path parameters")
	}
	for i := range result {
		result[i] = float64(out[i])
	}
	return result, nil
}

// NegotiateShortcuts returns owned action/key/modifier/assigned rows without a scene.
func NegotiateShortcuts(actions []uint32, candidates, host [][3]uint32) ([][4]uint32, error) {
	if len(actions) > 64 || len(candidates) > 256 || len(host) > 256 {
		return nil, errors.New("Shortcut table capacity")
	}
	var a, c, h *C.uint32_t
	if len(actions) > 0 {
		a = (*C.uint32_t)(unsafe.Pointer(&actions[0]))
	}
	if len(candidates) > 0 {
		c = (*C.uint32_t)(unsafe.Pointer(&candidates[0]))
	}
	if len(host) > 0 {
		h = (*C.uint32_t)(unsafe.Pointer(&host[0]))
	}
	out := make([][4]uint32, len(actions))
	var o *C.uint32_t
	if len(out) > 0 {
		o = (*C.uint32_t)(unsafe.Pointer(&out[0]))
	}
	n := C.nrNegotiateShortcuts(a, C.uint32_t(len(actions)), c, C.uint32_t(len(candidates)), h, C.uint32_t(len(host)), o, C.uint32_t(len(actions)))
	if n < 0 {
		return nil, errors.New("Invalid shortcut capabilities/preferences")
	}
	return out, nil
}

// AngularDragExchange uses diagonal inertias in one explicit shared principal frame.
func (s *Scene) AngularDragExchange(bodyInertia, waterInertia, conductance [3]float64, seconds float64, bodyOmega, waterOmega [3]float64) ([10]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var result [10]float64
	if s.context == nil {
		return result, errors.New("closed")
	}
	var out [10]C.double
	if C.nrAngularDragExchange((*C.double)(unsafe.Pointer(&bodyInertia[0])), (*C.double)(unsafe.Pointer(&waterInertia[0])), (*C.double)(unsafe.Pointer(&conductance[0])), C.double(seconds), (*C.double)(unsafe.Pointer(&bodyOmega[0])), (*C.double)(unsafe.Pointer(&waterOmega[0])), &out[0], 10) != 1 {
		return result, errors.New("invalid finite-inertia angular exchange")
	}
	for i := range result {
		result[i] = float64(out[i])
	}
	return result, nil
}

// FluidDragExchange returns final velocities, water impulse XYZ and dissipated energy.
func (s *Scene) FluidDragExchange(bodyMass, waterMass, conductance, seconds float64, bodyVelocity, waterVelocity [3]float64) ([10]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var result [10]float64
	if s.context == nil {
		return result, errors.New("closed")
	}
	var out [10]C.double
	if C.nrFluidDragExchange(C.double(bodyMass), C.double(waterMass), C.double(conductance), C.double(seconds), (*C.double)(unsafe.Pointer(&bodyVelocity[0])), (*C.double)(unsafe.Pointer(&waterVelocity[0])), &out[0], 10) != 1 {
		return result, errors.New("invalid finite-mass drag parameters")
	}
	for i := range result {
		result[i] = float64(out[i])
	}
	return result, nil
}

// HullImmersionPlane returns an owned volume/centroid row for an oriented half-space.
func (s *Scene) HullImmersionPlane(vertices [][3]float64, faces [][3]uint32, point, normal [3]float64) ([5]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var result [5]float64
	if s.context == nil {
		return result, errors.New("closed")
	}
	if len(vertices) < 4 || len(vertices) > 128 || len(faces) < 4 || len(faces) > 256 {
		return result, errors.New("hull size")
	}
	var out [5]C.double
	if C.nrHullImmersionPlane((*C.double)(unsafe.Pointer(&vertices[0][0])), C.uint32_t(len(vertices)), (*C.uint32_t)(unsafe.Pointer(&faces[0][0])), C.uint32_t(len(faces)), (*C.double)(unsafe.Pointer(&point[0])), (*C.double)(unsafe.Pointer(&normal[0])), &out[0], 5) != 1 {
		return result, errors.New("invalid convex hull or plane")
	}
	for i := range result {
		result[i] = float64(out[i])
	}
	return result, nil
}

// HullBuoyancyPlane returns immersion, net force and torque; lift remains vertical.
func (s *Scene) HullBuoyancyPlane(vertices [][3]float64, faces [][3]uint32, point, normal [3]float64, density, gravity, mass float64, centerOfMass [3]float64) ([11]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var result [11]float64
	if s.context == nil {
		return result, errors.New("closed")
	}
	if len(vertices) < 4 || len(vertices) > 128 || len(faces) < 4 || len(faces) > 256 {
		return result, errors.New("hull size")
	}
	var out [11]C.double
	if C.nrHullBuoyancyPlane((*C.double)(unsafe.Pointer(&vertices[0][0])), C.uint32_t(len(vertices)), (*C.uint32_t)(unsafe.Pointer(&faces[0][0])), C.uint32_t(len(faces)), (*C.double)(unsafe.Pointer(&point[0])), (*C.double)(unsafe.Pointer(&normal[0])), C.double(density), C.double(gravity), C.double(mass), (*C.double)(unsafe.Pointer(&centerOfMass[0])), &out[0], 11) != 1 {
		return result, errors.New("invalid hull buoyancy parameters")
	}
	for i := range result {
		result[i] = float64(out[i])
	}
	return result, nil
}

// HullImmersion returns owned total/submerged volumes and submerged centroid XYZ.
func (s *Scene) HullImmersion(vertices [][3]float64, faces [][3]uint32, height float64) ([5]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var result [5]float64
	if s.context == nil {
		return result, errors.New("closed")
	}
	if len(vertices) < 4 || len(vertices) > 128 || len(faces) < 4 || len(faces) > 256 {
		return result, errors.New("hull size")
	}
	var out [5]C.double
	if C.nrHullImmersion((*C.double)(unsafe.Pointer(&vertices[0][0])), C.uint32_t(len(vertices)), (*C.uint32_t)(unsafe.Pointer(&faces[0][0])), C.uint32_t(len(faces)), C.double(height), &out[0], 5) != 1 {
		return result, errors.New("invalid convex hull")
	}
	for i := range result {
		result[i] = float64(out[i])
	}
	return result, nil
}

// FloatHull copies quaternion, local angular velocity/inertia/center, and volume.
func (s *Scene) FloatHull(id uint32) (*[14]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	var out [14]C.double
	status := C.nrFloatHull(s.context, C.uint32_t(id), &out[0], 14)
	if status < 0 {
		return nil, errors.New("invalid hull query")
	}
	if status == 0 {
		return nil, nil
	}
	row := new([14]float64)
	for i := range row {
		row[i] = float64(out[i])
	}
	return row, nil
}

// HullMeshImmersion returns owned volumes/centroid for disjoint water triangles.
func (s *Scene) HullMeshImmersion(vertices [][3]float64, faces [][3]uint32, water [][9]float64) ([5]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	var result [5]float64
	if s.context == nil {
		return result, errors.New("closed")
	}
	if len(vertices) < 4 || len(vertices) > 128 || len(faces) < 4 || len(faces) > 256 || len(water) < 1 || len(water) > 256 {
		return result, errors.New("hull/surface size")
	}
	var out [5]C.double
	if C.nrHullMeshImmersion((*C.double)(unsafe.Pointer(&vertices[0][0])), C.uint32_t(len(vertices)), (*C.uint32_t)(unsafe.Pointer(&faces[0][0])), C.uint32_t(len(faces)), (*C.double)(unsafe.Pointer(&water[0][0])), C.uint32_t(len(water)), &out[0], 5) != 1 {
		return result, errors.New("invalid hull/surface mesh")
	}
	for i := range result {
		result[i] = float64(out[i])
	}
	return result, nil
}

// SurfaceFluid returns an owned finite water momentum/energy record, or nil.
func (s *Scene) SurfaceFluidAngular(id uint32) (*[12]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	var out [12]C.double
	status := C.nrSurfaceFluidAngular(s.context, C.uint32_t(id), &out[0], 12)
	if status < 0 {
		return nil, errors.New("invalid angular fluid query")
	}
	if status == 0 {
		return nil, nil
	}
	var result [12]float64
	for i := range result {
		result[i] = float64(out[i])
	}
	return &result, nil
}
func (s *Scene) SurfaceFluid(id uint32) (*[15]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	var out [15]C.double
	status := C.nrSurfaceFluid(s.context, C.uint32_t(id), &out[0], 15)
	if status < 0 {
		return nil, errors.New("invalid finite water query")
	}
	if status == 0 {
		return nil, nil
	}
	row := new([15]float64)
	for i := range row {
		row[i] = float64(out[i])
	}
	return row, nil
}

// ScriptRun owns a logical whole-grapheme source span and its ISO15924 tag.
type ScriptRun struct {
	Start, End uint32
	Script     string
}

// BidiLines owns seven-word visual rows for caller-selected font line ends.
func (s *Scene) BidiLines(text string, ends []uint32, direction uint32) ([][7]uint32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	if !utf8.ValidString(text) || len(ends) > 2048 || direction > 2 {
		return nil, errors.New("invalid explicit lines")
	}
	values := []rune(text)
	if len(values) > 2048 {
		return nil, errors.New("text capacity")
	}
	input := make([]C.uint32_t, len(values))
	for i, c := range values {
		input[i] = C.uint32_t(c)
	}
	lines := make([]C.uint32_t, len(ends))
	for i, end := range ends {
		lines[i] = C.uint32_t(end)
	}
	out := make([]C.uint32_t, len(values)*7)
	var source, boundaries, output *C.uint32_t
	if len(input) > 0 {
		source = &input[0]
	}
	if len(lines) > 0 {
		boundaries = &lines[0]
	}
	if len(out) > 0 {
		output = &out[0]
	}
	count := C.nrBidiClusterLines(source, C.uint32_t(len(values)), boundaries, C.uint32_t(len(lines)), C.uint32_t(direction), output, C.uint32_t(len(values)))
	if count < 0 {
		return nil, errors.New("invalid grapheme or hard-break line boundary")
	}
	rows := make([][7]uint32, int(count))
	for i := range rows {
		for j := range rows[i] {
			rows[i][j] = uint32(out[i*7+j])
		}
	}
	return rows, nil
}
func (s *Scene) ScriptRuns(text string) ([]ScriptRun, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	if !utf8.ValidString(text) {
		return nil, errors.New("invalid UTF8")
	}
	values := []rune(text)
	if len(values) > 2048 {
		return nil, errors.New("script capacity")
	}
	input := make([]C.uint32_t, len(values))
	for i, c := range values {
		input[i] = C.uint32_t(c)
	}
	var pointer *C.uint32_t
	if len(input) > 0 {
		pointer = &input[0]
	}
	out := make([]C.uint32_t, len(values)*3)
	var output *C.uint32_t
	if len(out) > 0 {
		output = &out[0]
	}
	count := C.nrScriptRuns(pointer, C.uint32_t(len(values)), output, C.uint32_t(len(values)))
	if count < 0 {
		return nil, errors.New("invalid Unicode scalar")
	}
	rows := make([]ScriptRun, int(count))
	for i := range rows {
		tag := uint32(out[3*i+2])
		rows[i] = ScriptRun{uint32(out[3*i]), uint32(out[3*i+1]), string([]byte{byte(tag >> 24), byte(tag >> 16), byte(tag >> 8), byte(tag)})}
	}
	return rows, nil
}

func (s *Scene) PromptVisualLayout() ([][10]float64, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	n := int(C.nrPromptVisualLayout(s.context, nil, 0))
	if n < 0 {
		return nil, errors.New("invalid prompt layout")
	}
	rows := make([][10]float64, n)
	if n > 0 && int(C.nrPromptVisualLayout(s.context, (*C.double)(unsafe.Pointer(&rows[0][0])), C.uint32_t(n))) != n {
		return nil, errors.New("invalid prompt layout")
	}
	return rows, nil
}

// SourceStageHit owns the original semantic ID and zero-based subitem.
type SourceStageHit struct {
	ID   int32
	Item int32
}

func (s *Scene) SourceStageTween(from, to int32, elapsed uint64, duration uint32, easing int32) (int32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil || easing < 0 || easing > 3 {
		return 0, errors.New("invalid source Stage tween")
	}
	return int32(C.nrSourceStageTween(C.int32_t(from), C.int32_t(to), C.uint64_t(elapsed), C.uint32_t(duration), C.int32_t(easing))), nil
}
func (s *Scene) SourceStageInkOpacity(age, fade uint32, row, band, minimum int32) (int32, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return 0, errors.New("closed")
	}
	v := C.nrSourceStageInkOpacity(C.uint32_t(age), C.uint32_t(fade), C.int32_t(row), C.int32_t(band), C.int32_t(minimum))
	if v < 0 {
		return 0, errors.New("invalid source Stage opacity")
	}
	return int32(v), nil
}
func (s *Scene) SourceStageHit(x, y int32) (*SourceStageHit, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	var out [2]C.int32_t
	r := C.nrSourceStageHit(s.context, C.int32_t(x), C.int32_t(y), &out[0], 2)
	if r < 0 {
		return nil, errors.New("invalid source Stage hit")
	}
	if r == 0 {
		return nil, nil
	}
	return &SourceStageHit{int32(out[0]), int32(out[1])}, nil
}
