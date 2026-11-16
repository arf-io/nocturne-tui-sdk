package main

import (
	"bytes"
	"encoding/json"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestLargeInputAndUnterminatedFinalLine(t *testing.T) {
	binary := filepath.Join(t.TempDir(), "actual-command")
	build := exec.Command("go", "build", "-o", binary, ".")
	if output, err := build.CombinedOutput(); err != nil {
		t.Fatalf("build: %v: %s", err, output)
	}
	text := strings.Repeat("λ", 70001)
	payload := map[string]any{"op": "draft", "text": text, "emitWeather": false}
	raw, err := json.Marshal(payload)
	if err != nil {
		t.Fatal(err)
	}
	for _, newline := range []bool{false, true} {
		input := append([]byte(nil), raw...)
		if newline {
			input = append(input, '\n')
		}
		cmd := exec.Command(binary)
		cmd.Stdin = bytes.NewReader(input)
		output, err := cmd.Output()
		if err != nil {
			t.Fatalf("actual command: %v", err)
		}
		var result struct {
			Metadata struct{ Prompt struct{ Text string } }
		}
		if err := json.Unmarshal(output, &result); err != nil {
			t.Fatal(err)
		}
		if result.Metadata.Prompt.Text != text {
			t.Fatalf("text changed: got %d bytes, want %d", len(result.Metadata.Prompt.Text), len(text))
		}
	}
}
