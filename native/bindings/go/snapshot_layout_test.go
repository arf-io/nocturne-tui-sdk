package native

import (
	"compress/gzip"
	"encoding/binary"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func readSnapshotFixture(t *testing.T, name string) []byte {
	t.Helper()
	f, err := os.Open(filepath.Join("..", "..", "tests", "fixtures", name))
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	z, err := gzip.NewReader(f)
	if err != nil {
		t.Fatal(err)
	}
	defer z.Close()
	b, err := io.ReadAll(z)
	if err != nil {
		t.Fatal(err)
	}
	return b
}

func TestRestoreContracts7ExpandedSchema03AndPromote(t *testing.T) {
	fixture := readSnapshotFixture(t, "schema-20261003-contracts7-registered-style.snapshot.gz")
	if binary.LittleEndian.Uint32(fixture[12:16]) != 0x20261003 || binary.LittleEndian.Uint32(fixture[16:20]) != 4_498_608 {
		t.Fatal("fixture version/length changed")
	}
	s, err := New(77)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	if err := s.Restore(fixture); err != nil {
		t.Fatal(err)
	}
	info, err := s.Info()
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(info), `"path":"/lab/one"`) || !strings.Contains(string(info), `"styleRules"`) {
		t.Fatalf("selector state lost: %s", info)
	}
	out, err := s.Snapshot()
	if err != nil {
		t.Fatal(err)
	}
	assertCurrentSnapshot(t, s, out)
}

func TestRestoreLocalIntentActionSchema04AndRejectWrongExpandedPair(t *testing.T) {
	fixture := readSnapshotFixture(t, "schema-20261004-intent-action.snapshot.gz")
	s, err := New(78)
	if err != nil {
		t.Fatal(err)
	}
	defer s.Close()
	if err := s.Restore(fixture); err != nil {
		t.Fatal(err)
	}
	info, err := s.Info()
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(info), `"valueSource":"intentValue"`) {
		t.Fatalf("intent action lost: %s", info)
	}
	bad := readSnapshotFixture(t, "schema-20261003-contracts7-registered-style.snapshot.gz")
	binary.LittleEndian.PutUint32(bad[12:16], 0x20261004)
	if err := s.Restore(bad); err == nil {
		t.Fatal("expanded schema-03 accepted under local schema-04 meaning")
	}
}
