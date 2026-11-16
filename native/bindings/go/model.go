package native

/*
#include <stdlib.h>
#include "nocturne_native.h"
static void *nrModelOwnedMalloc(size_t size){return malloc(size);}
*/
import "C"
import (
	"encoding/binary"
	"errors"
	"unsafe"
)

func (s *Scene) ensureModelMemory() error {
	required := C.nrModelMemorySize(s.context)
	if required <= C.nrModelMemoryCapacity(s.context) {
		return errors.New("model storage request made no progress")
	}
	if uint64(required) > uint64(^uintptr(0)) {
		return errors.New("model exceeds address space")
	}
	memory := C.nrModelOwnedMalloc(C.size_t(required))
	if memory == nil {
		return errors.New("model allocation failed")
	}
	if C.nrSetModelMemory(s.context, memory, required) != 0 {
		C.free(memory)
		return errors.New("model storage rejected")
	}
	C.free(s.modelMemory)
	s.modelMemory = memory
	return nil
}

// SetModelRecords atomically uploads original Q8/RGB geometry, outside JSON transactions.
func (s *Scene) SetModelRecords(data []byte) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return errors.New("closed")
	}
	if len(data)%40 != 0 || uint64(len(data)) > uint64(^uint32(0)) {
		return errors.New("model record length")
	}
	// Own aligned C words even when the caller supplied an unaligned byte slice.
	words := make([]uint32, len(data)/4)
	for i := range words {
		words[i] = binary.LittleEndian.Uint32(data[i*4 : i*4+4])
	}
	var ptr *C.NrModelTriangle
	if len(words) > 0 {
		ptr = (*C.NrModelTriangle)(unsafe.Pointer(&words[0]))
	}
	for {
		code := C.nrModelSet(s.context, ptr, C.uint32_t(len(data)/40))
		if code == 0 {
			return nil
		}
		message := C.GoString(C.nrError(s.context))
		if message != "Model storage required" {
			return errors.New(message)
		}
		if e := s.ensureModelMemory(); e != nil {
			return e
		}
	}
}

// ModelRecords returns an owned copy of canonical original geometry.
func (s *Scene) ModelRecords() ([]byte, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.context == nil {
		return nil, errors.New("closed")
	}
	count := C.nrModelTriangleCount(s.context)
	size := uint64(count) * 40
	if size > uint64(int(^uint(0)>>1)) {
		return nil, errors.New("model exceeds address space")
	}
	data := make([]byte, int(size))
	var ptr *C.NrModelTriangle
	if len(data) > 0 {
		ptr = (*C.NrModelTriangle)(unsafe.Pointer(&data[0]))
	}
	if C.nrModelCopy(s.context, ptr, count) != C.int(count) {
		return nil, errors.New("model copy rejected")
	}
	return data, nil
}
