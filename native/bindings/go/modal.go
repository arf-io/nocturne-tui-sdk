package native
/*
#include <stdlib.h>
#include "nocturne_native.h"
static void *nrModalOwnedMalloc(size_t size){return malloc(size);}
*/
import "C"
import "errors"
func (s *Scene) ensureModalMemory() error {
	required := C.nrModalMemorySize(s.context)
	if required <= C.nrModalMemoryCapacity(s.context) {
		return errors.New("modal storage request made no progress")
	}
	if uint64(required) > uint64(^uintptr(0)) {
		return errors.New("modal exceeds address space")
	}
	memory := C.nrModalOwnedMalloc(C.size_t(required))
	if memory == nil {
		return errors.New("modal allocation failed")
	}
	if C.nrSetModalMemory(s.context, memory, required) != 0 {
		C.free(memory)
		return errors.New("modal storage rejected")
	}
	C.free(s.modalMemory)
	s.modalMemory = memory
	return nil
}


func SourceStageOklch(lightness,chroma,hue int32)(uint32,error){if lightness<0||lightness>1000||chroma<0||chroma>4000{return 0,errors.New("original source color domain")};return uint32(C.nrSourceStageOklch(C.int32_t(lightness),C.int32_t(chroma),C.int32_t(hue))),nil}
