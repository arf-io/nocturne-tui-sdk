// Render an ANSI snapshot. The host remains responsible for terminal ownership.
package main

import (
	"fmt"
	nocturne "nocturne.local/surfaces"
	"os"
	"strings"
)

func run() error {
	surface, err := nocturne.NewSurface()
	if err != nil {
		return err
	}
	for name, value := range map[string]int32{"width": 80, "height": 24, "layout": 1, "effect": 3} {
		if err = surface.Set(name, value); err != nil {
			return err
		}
	}
	frame, err := surface.Render(6000, "hello from Go")
	if err != nil {
		return err
	}
	var output strings.Builder
	for index, cell := range frame.Cells {
		fmt.Fprintf(&output, "\x1b[38;2;%d;%d;%dm\x1b[48;2;%d;%d;%dm%c",
			cell.Fg>>16, (cell.Fg>>8)&255, cell.Fg&255,
			cell.Bg>>16, (cell.Bg>>8)&255, cell.Bg&255, rune(cell.Glyph))
		if (index+1)%frame.Width == 0 {
			output.WriteString("\x1b[0m\n")
		}
	}
	_, err = fmt.Print(output.String())
	return err
}
func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, "Nocturne:", err)
		os.Exit(1)
	}
}
