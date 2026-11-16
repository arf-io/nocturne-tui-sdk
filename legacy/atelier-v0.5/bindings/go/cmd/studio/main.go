// Standalone snapshot host; embedders should consume Frame.Cells instead of ANSI.
package main

import (
	"fmt"
	n "nocturne.local/surfaces"
	"os"
)

func main() {
	s, e := n.NewStudio()
	if e != nil {
		panic(e)
	}
	_ = s.Set("width", 80)
	_ = s.Set("height", 24)
	_ = s.Set("pattern", 3)
	_ = s.Set("focusMode", 1)
	_ = s.Set("focusY", 12*256)
	node, _ := n.NewStudioNode("progress", 5, 12, 65, 2)
	_ = node.Set("value", 670)
	_ = node.Set("colorAnimation", 2)
	frame, e := s.Render(2500, []n.StudioNode{node}, []n.StudioImpulse{{XQ8: 20 * 256, YQ8: 12 * 256, Strength: 1000, AtMs: 1700}})
	if e != nil {
		panic(e)
	}
	for y := 0; y < frame.Height; y++ {
		fmt.Fprintf(os.Stdout, "\x1b[%d;1H", y+1)
		for _, c := range frame.Cells[y*frame.Width : (y+1)*frame.Width] {
			fmt.Fprintf(os.Stdout, "\x1b[38;2;%d;%d;%dm\x1b[48;2;%d;%d;%dm%c", c.Fg>>16, c.Fg>>8&255, c.Fg&255, c.Bg>>16, c.Bg>>8&255, c.Bg&255, rune(c.Glyph))
		}
	}
	fmt.Print("\x1b[0m\n")
}
