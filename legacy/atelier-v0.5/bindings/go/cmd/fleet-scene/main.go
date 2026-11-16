// Render and fingerprint one exported Fleet scene without a terminal session.
package main

import (
	"crypto/sha256"
	"fmt"
	nocturne "nocturne.local/surfaces"
	"os"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: go run ./cmd/fleet-scene /path/scene.json")
		os.Exit(2)
	}
	b, e := os.ReadFile(os.Args[1])
	if e != nil {
		panic(e)
	}
	f, e := nocturne.RenderFleetScene(b)
	if e != nil {
		panic(e)
	}
	fmt.Printf("%x\n", sha256.Sum256(f.Bytes()))
}
