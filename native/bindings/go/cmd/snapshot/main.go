// Standalone current C-ABI example; no Node or subprocess path.
package main

import (
	"fmt"
	native "nocturne/native"
	"os"
)

func main() {
	s, e := native.New(2030)
	if e != nil {
		panic(e)
	}
	defer s.Close()
	if _, e = s.Command(map[string]any{"op": "emitter", "id": 1, "effect": "weather/autumn-drift", "count": 40}); e != nil {
		panic(e)
	}
	if e = s.AdvanceTo(900000); e != nil {
		panic(e)
	}
	f, e := s.Render()
	if e != nil {
		panic(e)
	}
	if e = os.WriteFile("preview.cells", f.Bytes, 0600); e != nil {
		panic(e)
	}
	info, e := s.Info()
	if e != nil {
		panic(e)
	}
	fmt.Println(string(info))
}
