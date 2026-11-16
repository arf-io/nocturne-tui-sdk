package native

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"
)

func TestCompleteMetadataOwnedUnicodeAndPure(t *testing.T) {
	s, e := New(8128)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	legacy, e := s.Info()
	if e != nil {
		t.Fatal(e)
	}
	complete, e := s.InfoComplete()
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(legacy, complete) {
		t.Fatal("small metadata differs")
	}
	if _, e = s.Command(map[string]any{"op": "pause", "paused": true}); e != nil {
		t.Fatal(e)
	}
	text := strings.Repeat("🙂", 2048)
	for id := 1; id <= 24; id++ {
		if _, e = s.Command(map[string]any{"op": "text", "id": id, "text": text}); e != nil {
			t.Fatal(e)
		}
	}
	for id := 1; id <= 12; id++ {
		if _, e = s.Command(map[string]any{"op": "window", "id": id, "title": "Retained " + string(rune('A'+id)), "text": text, "position": []int{0, 0, 16000}}); e != nil {
			t.Fatal(e)
		}
	}
	largePrompt := strings.Repeat("界", 400001)
	if _, e = s.Command(map[string]any{"op": "draft", "text": largePrompt, "emitWeather": false}); e != nil {
		t.Fatal(e)
	}
	before, e := s.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	legacy, e = s.Info()
	if e != nil {
		t.Fatal(e)
	}
	complete, e = s.InfoComplete()
	if e != nil {
		t.Fatal(e)
	}
	if string(legacy) != `{"error":"metadata capacity exceeded"}` && !bytes.Equal(legacy, complete) {
		t.Fatal("bounded metadata neither complete nor capacity error")
	}
	if !bytes.Contains(complete, []byte(largePrompt)) {
		t.Fatal("large prompt source lost")
	}
	if len(complete) <= 1048576 || !json.Valid(complete) || strings.Count(string(complete), text) != 36 {
		t.Fatal("incomplete Unicode source")
	}
	after, e := s.Snapshot()
	if e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(before, after) {
		t.Fatal("reader changed source")
	}
	s.Close()
	if _, e = s.InfoComplete(); e == nil {
		t.Fatal("closed context accepted")
	}
}

func TestCompleteMetadataBeyond16MiB(t *testing.T) {
	s, e := New(8128)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	source := strings.Repeat("\x0b", 2800001)
	if _, e = s.Command(map[string]any{"op": "draft", "text": source, "emitWeather": false}); e != nil {
		t.Fatal(e)
	}
	complete, e := s.InfoComplete()
	if e != nil {
		t.Fatal(e)
	}
	if len(complete) <= 16777216 {
		t.Fatal("metadata did not cross old limit")
	}
	var info struct {
		Prompt struct {
			Text  string
			Caret int
		}
	}
	if e = json.Unmarshal(complete, &info); e != nil {
		t.Fatal(e)
	}
	if info.Prompt.Text != source || info.Prompt.Caret != len(source) {
		t.Fatal("large metadata source/caret lost")
	}
	t.Logf("Actual complete metadata bytes=%d scalars=%d", len(complete), len(source))
}
