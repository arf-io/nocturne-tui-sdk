package main

import (
	"encoding/json"
	"fmt"
	tea "github.com/charmbracelet/bubbletea"
	"strings"
)

type documentInfo struct {
	InputOwner string `json:"inputOwner"`
	Prompt     struct {
		Anchor int `json:"anchor"`
		Caret  int `json:"caret"`
	} `json:"prompt"`
}

func (m *model) documentState() (documentInfo, string, bool) {
	var info documentInfo
	raw, err := m.scene.InfoComplete()
	if err == nil {
		err = json.Unmarshal(raw, &info)
	}
	if err != nil {
		m.err = err
		return info, "", false
	}
	if info.InputOwner != "prompt" {
		return info, "", false
	}
	source, err := m.scene.TextRunSource(0, 0)
	if err != nil {
		m.err = err
		return info, "", false
	}
	return info, source, true
}

// The native layout owns Unicode resolution and cell geometry. Bubble Tea owns
// the cached lines and viewport; source text is never reconstructed from cells.
func (m *model) paintDocument() bool {
	info, source, active := m.documentState()
	if !active {
		return false
	}
	width, height := max(1, m.documentWidth), max(1, m.documentHeight)
	layout, err := m.scene.DocumentLayout(source, uint32(width), 2, 1)
	if err != nil {
		m.err = err
		return true
	}
	caret, caretErr := m.documentCaret(source, info.Prompt.Caret)
	signature := documentSignature{source, info.Prompt.Caret, width, height}
	if m.documentLast == nil || m.documentLast.source != source {
		m.documentPreferred = nil
	}
	bottom := 0
	for _, cell := range layout {
		bottom = max(bottom, int(cell[3]))
	}
	if caretErr == nil {
		bottom = max(bottom, int(caret[1]))
	}
	if caretErr == nil && (m.documentLast == nil || *m.documentLast != signature) {
		y := int(caret[1])
		if y < m.documentScroll {
			m.documentScroll = y
		} else if y >= m.documentScroll+max(1, height-1) {
			m.documentScroll = max(0, y-max(1, height-1)+1)
		}
	}
	m.documentScroll = min(m.documentScroll, max(0, bottom-max(1, height-1)+1))
	m.documentLast = &signature
	rows := make([]strings.Builder, height)
	title := []rune("NOCTURNE Unicode document")
	rows[0].WriteString(string(title[:min(width, len(title))]))
	scalars := []rune(source)
	for _, cell := range layout {
		y := int(cell[3]) - m.documentScroll + 1
		if y < 1 || y >= height || cell[2]+cell[4] > uint32(width) {
			continue
		}
		cluster := append([]rune(nil), scalars[cell[0]:cell[1]]...)
		if len(cluster) > 0 {
			cluster[0] = rune(cell[6])
		}
		text := strings.Map(func(r rune) rune {
			if r == '\t' {
				return ' '
			}
			if r < 32 || r >= 127 && r < 160 {
				return -1
			}
			return r
		}, string(cluster))
		if len(cluster) == 1 && cluster[0] == '\t' {
			text = strings.Repeat(" ", int(cell[4]))
		}
		selected := info.Prompt.Anchor >= 0 && int(cell[0]) < max(info.Prompt.Anchor, info.Prompt.Caret) && int(cell[1]) > min(info.Prompt.Anchor, info.Prompt.Caret)
		if selected {
			rows[y].WriteString("\x1b[48;2;67;99;127m")
		}
		rows[y].WriteString(text)
		if selected {
			rows[y].WriteString("\x1b[0m")
		}
	}
	lines := make([]string, height)
	for i := range rows {
		lines[i] = rows[i].String()
	}
	m.view = strings.Join(lines, "\n")
	return true
}
func(m *model)cancelDocumentDrag(){m.documentDrag=nil;m.documentIdentity=nil}
func(m *model)captureDocumentDrag(source string,offset uint32){
 rows,e:=m.scene.TextRunClusters(0,0);if e!=nil{m.err=e;m.cancelDocumentDrag();return}
 boundaries,e:=m.scene.DocumentBoundaries(source);if e!=nil{m.err=e;m.cancelDocumentDrag();return}
 anchor:=uint32(0);for _,b:=range boundaries{if b<=offset{anchor=b}else{break}}
 m.documentDrag=&anchor;m.documentIdentity=&documentAnchor{}
 if len(rows)==0{return}
 row:=rows[len(rows)-1];for _,r:=range rows{if r[1]==anchor{row=r;break}}
 runes:=[]rune(source);m.documentIdentity=&documentAnchor{identity:row[0],generation:row[3],end:row[1]!=anchor,source:string(runes[row[1]:row[2]])}
}
func(m *model)resolveDocumentDrag(source string)*uint32{
 if m.documentDrag==nil{return nil};q:=m.documentIdentity;if q==nil{m.cancelDocumentDrag();return nil}
 if q.identity==0{if source!=""{m.cancelDocumentDrag();return nil};return m.documentDrag}
 rows,e:=m.scene.TextRunClusters(0,0);if e!=nil{m.err=e;m.cancelDocumentDrag();return nil};runes:=[]rune(source)
 for _,r:=range rows{if r[0]==q.identity&&r[3]==q.generation&&string(runes[r[1]:r[2]])==q.source{offset:=r[1];if q.end{offset=r[2]};m.documentDrag=&offset;return m.documentDrag}}
 m.cancelDocumentDrag();return nil
}
func (m *model) documentMouse(msg tea.MouseMsg) bool {
	info, source, active := m.documentState()
	if !active {
        m.cancelDocumentDrag()
		return false
	}
	if msg.Y<1||(m.documentHeight>0&&msg.Y>=m.documentHeight){if msg.Action==tea.MouseActionRelease{m.cancelDocumentDrag()};return true}
	width := max(1, m.documentWidth)
	if msg.Button == tea.MouseButtonWheelUp || msg.Button == tea.MouseButtonWheelDown {
		layout, err := m.scene.DocumentLayout(source, uint32(width), 2, 1)
		if err != nil {
			m.err = err
			return true
		}
		last := 0
		for _, cell := range layout {
			last = max(last, int(cell[3]))
		}
		delta := 3
		if msg.Button == tea.MouseButtonWheelUp {
			delta = -3
		}
		m.documentScroll = min(max(0, last-max(1, m.documentHeight-1)+1), max(0, m.documentScroll+delta))
		return true
	}
	if msg.Y < 1 || (msg.Button != tea.MouseButtonLeft && m.documentDrag == nil) {
		return true
	}
	offset, err := m.scene.DocumentHit(source, uint32(width), uint32(max(0, msg.X)), uint32(msg.Y-1+m.documentScroll), 2, 1)
	if err != nil {
		m.err = fmt.Errorf("document pointer: %w", err)
		return true
	}
	if msg.Action == tea.MouseActionPress {
		anchor := offset
		if msg.Shift {
			anchor = uint32(max(0, info.Prompt.Caret))
			if info.Prompt.Anchor >= 0 {
				anchor = uint32(info.Prompt.Anchor)
			}
		}
		m.captureDocumentDrag(source,anchor)
		m.documentPreferred = nil
	}
	if anchor:=m.resolveDocumentDrag(source);anchor!=nil {
		m.apply(map[string]any{"op": "select", "anchor": *anchor, "caret": offset, "unit": "grapheme"})
	}
	if msg.Action == tea.MouseActionRelease {
		m.cancelDocumentDrag()
	}
	return true
}

func (m *model) documentCaret(source string, offset int) ([3]uint32, error) {
	boundaries, err := m.scene.DocumentBoundaries(source)
	if err != nil {
		return [3]uint32{}, err
	}
	snapped := uint32(0)
	for _, b := range boundaries {
		if int(b) <= offset {
			snapped = b
		}
	}
	return m.scene.DocumentCaret(source, uint32(max(1, m.documentWidth)), snapped, 1, 2, 1)
}
func (m *model) documentMove(key string, shift bool) bool {
	switch key {
	case "left", "right", "up", "down", "home", "end", "pgup", "pgdown":
	default:
		return false
	}
	info, source, active := m.documentState()
	if !active {
		return false
	}
	caret, err := m.documentCaret(source, info.Prompt.Caret)
	if err != nil {
		m.err = err
		return true
	}
	x, y := int(caret[0]), int(caret[1])
	switch key {
	case "up", "down", "pgup", "pgdown":
		if m.documentPreferred == nil {
			m.documentPreferred = &x
		}
		x = *m.documentPreferred
		step := 1
		if key == "pgup" || key == "pgdown" {
			step = max(1, m.documentHeight-1)
		}
		if key == "up" || key == "pgup" {
			y -= step
		} else {
			y += step
		}
	case "home":
		m.documentPreferred = nil
		x = 0
	case "end":
		m.documentPreferred = nil
		x = max(1, m.documentWidth)
	case "left":
		m.documentPreferred = nil
		x--
	case "right":
		m.documentPreferred = nil
		x++
	}
	offset, err := m.scene.DocumentHit(source, uint32(max(1, m.documentWidth)), uint32(max(0, x)), uint32(max(0, y)), 2, 1)
	if err != nil {
		m.err = err
		return true
	}
	anchor := offset
	if shift {
		anchor = uint32(max(0, info.Prompt.Caret))
		if info.Prompt.Anchor >= 0 {
			anchor = uint32(info.Prompt.Anchor)
		}
	}
	boundaries, err := m.scene.DocumentBoundaries(source)
	if err != nil {
		m.err = err
		return true
	}
	snapped := uint32(0)
	for _, b := range boundaries {
		if b <= anchor {
			snapped = b
		}
	}
	m.apply(map[string]any{"op": "select", "anchor": snapped, "caret": offset, "unit": "grapheme"})
	return true
}
