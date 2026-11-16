package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	native "nocturne/native"
	"os"
)

func main() {
	s, err := native.New(2030)
	if err != nil {
		panic(err)
	}
	defer s.Close()
	scan := bufio.NewScanner(os.Stdin)
	scan.Buffer(make([]byte, 4096), 65536)
	index := 0
	for scan.Scan() {
		var input struct {
			Text string `json:"text"`
		}
		if err = json.Unmarshal(scan.Bytes(), &input); err != nil {
			panic(err)
		}
		boundaries, e := s.GraphemeBoundaries(input.Text)
		if e != nil {
			panic(e)
		}
		widths1, e := s.GraphemeWidths(input.Text, 1)
		if e != nil {
			panic(e)
		}
		widths2, e := s.GraphemeWidths(input.Text, 2)
		if e != nil {
			panic(e)
		}
		layouts := make([][][5]uint32, 0, 6)
		for _, columns := range []uint32{1, 3, 8} {
			for _, policy := range []uint32{1, 2} {
				layout, err := s.GraphemeLayout(input.Text, columns, policy)
				if err != nil {
					panic(err)
				}
				layouts = append(layouts, layout)
			}
		}
		b, e := json.Marshal(map[string]interface{}{"index": index, "boundaries": boundaries, "widths1": widths1, "widths2": widths2, "layouts": layouts})
		if e != nil {
			panic(e)
		}
		fmt.Println(string(b))
		index++
	}
	if err = scan.Err(); err != nil {
		panic(err)
	}
}
