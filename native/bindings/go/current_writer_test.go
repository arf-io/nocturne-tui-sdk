package native

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"hash/crc32"
	"testing"
)

// Current writer expectations come from the published runtime contract. Frozen
// historical input fixture versions and prefixes remain explicit in their tests.
func assertCurrentSnapshot(t *testing.T, s *Scene, data []byte) {
	t.Helper()
	raw, err := s.InfoComplete()
	if err != nil {
		t.Fatal(err)
	}
	var meta struct {
		Contract struct {
			ABI    uint32 `json:"abiVersion"`
			Schema uint32 `json:"snapshotSchema"`
			Source uint32 `json:"sourceSchema"`
			Bytes  uint32 `json:"snapshotCapacityBytes"`
		} `json:"contract"`
	}
	if err = json.Unmarshal(raw, &meta); err != nil {
		t.Fatal(err)
	}
	if len(data) < 32 || !bytes.Equal(data[:8], []byte("NRRC4SRC")) || meta.Contract.Schema == 0 {
		t.Fatal("invalid current snapshot contract")
	}
	if binary.LittleEndian.Uint32(data[8:]) != meta.Contract.ABI || binary.LittleEndian.Uint32(data[12:]) != meta.Contract.Schema || binary.LittleEndian.Uint32(data[28:]) != meta.Contract.Source || uint32(len(data)) != meta.Contract.Bytes || binary.LittleEndian.Uint32(data[16:]) != uint32(len(data)-24) || binary.LittleEndian.Uint32(data[20:]) != crc32.ChecksumIEEE(data[24:]) {
		t.Fatal("snapshot differs from published writer contract")
	}
	t.Logf("validated writer schema=%x bytes=%d", meta.Contract.Schema, len(data))
}
