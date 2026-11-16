package main

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	nr "nocturne/native"
	"os"
)

func digest(b []byte) string { h := sha256.Sum256(b); return hex.EncodeToString(h[:]) }
func main() {
	s, e := nr.New(2030)
	if e != nil {
		panic(e)
	}
	defer s.Close()
	in := bufio.NewReader(os.Stdin)
	index := 0
	for {
		cmd, readErr := in.ReadBytes('\n')
		if readErr != nil && readErr != io.EOF {
			panic(readErr)
		}
		if len(cmd) == 0 && readErr == io.EOF {
			break
		}
		code, e := s.CommandRaw(cmd)
		if e != nil {
			fmt.Fprintln(os.Stderr, e)
			os.Exit(1)
		}
		for code == 1 {
			code, e = s.CommandRaw(cmd)
			if e != nil {
				panic(e)
			}
		}
		f, e := s.Render()
		if e != nil {
			panic(e)
		}
		state, e := s.Snapshot()
		if e != nil {
			panic(e)
		}
		info, e := s.Info()
		if e != nil {
			panic(e)
		}
		motions, e := s.ParticleMotions()
		if e != nil {
			panic(e)
		}
		b, _ := json.Marshal(map[string]any{"index": index, "frame": digest(f.Bytes), "state": digest(state), "metadata": json.RawMessage(info), "motions": motions})
		fmt.Println(string(b))
		index++
	}
}
