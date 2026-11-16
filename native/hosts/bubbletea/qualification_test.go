// This test-only executable wraps the real host model and program lifecycle.
// No framework or scene is mocked. Failure injection uses actual input/PTY events.
package main

import (
	"bufio"
	"encoding/binary"
	"encoding/json"
	"fmt"
	tea "github.com/charmbracelet/bubbletea"
	native "nocturne/native"
	"os"
	"testing"
	"time"
)

type observedModel struct {
	inner    model
	trace    *os.File
	scenario string
	setup    bool
}

func (m observedModel) record(event string) {
	b, e := m.inner.scene.Info()
	if e != nil {
		panic(e)
	}
	f, e := m.inner.scene.Render()
	if e != nil {
		panic(e)
	}
	nodeHits := map[uint32][2]uint32{}
	for index := uint32(0); index < f.Width*f.Height; index++ {
		owner := binary.LittleEndian.Uint32(f.Bytes[index*16+12:])
		if owner&0xff000000 == 0x10000000 {
			if _, exists := nodeHits[owner&0xffff]; !exists {
				nodeHits[owner&0xffff] = [2]uint32{index % f.Width, index / f.Width}
			}
		}
	}
	line, e := json.Marshal(map[string]any{"event": event, "info": json.RawMessage(b), "width": f.Width, "height": f.Height, "nodeHits": nodeHits})
	if e != nil {
		panic(e)
	}
	stat, e := m.trace.Stat()
	if e != nil {
		panic(e)
	}
	if stat.Size()+int64(len(line)) > 16*1024*1024 {
		panic("trace bound")
	}
	if _, e = m.trace.Write(append(line, '\n')); e != nil {
		panic(e)
	}
}
func (m observedModel) Init() tea.Cmd { return m.inner.Init() }
func (m observedModel) View() string {
	if m.setup {
		m.record("setup-raw")
		b := []byte{0}
		for {
			n, e := os.Stdin.Read(b)
			if e != nil {
				panic(e)
			}
			if n == 1 && b[0] == 17 {
				panic("intentional partial-startup panic")
			}
		}
	}
	return m.inner.View()
}
func (m observedModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	if key, ok := msg.(tea.KeyMsg); ok && key.String() == "ctrl+q" {
		if m.scenario == "panic" {
			m.record("panic-requested")
			panic("intentional qualification panic")
		}
		if m.scenario == "error" {
			m.inner.apply(map[string]any{"op": "invalid-qualification-command"})
		}
	}
	out, cmd := m.inner.Update(msg)
	m.inner = out.(model)
	m.record(fmt.Sprintf("%T", msg))
	return m, cmd
}
func fixtureRun() (code int) {
	s, e := native.New(2030)
	if e != nil {
		fmt.Fprintln(os.Stderr, e)
		return 1
	}
	defer s.Close()
	trace, e := os.OpenFile(os.Getenv("NOCTURNE_TEST_TRACE"), os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0600)
	if e != nil {
		fmt.Fprintln(os.Stderr, e)
		return 1
	}
	defer trace.Close()
	scenario := os.Getenv("NOCTURNE_TEST_SCENARIO")
	m := model{scene: s, last: time.Now(), paused: scenario != "normal" && scenario != "backpressure"}
	input, e := os.Open(os.Getenv("NOCTURNE_TEST_FIXTURE"))
	if e != nil {
		fmt.Fprintln(os.Stderr, e)
		return 1
	}
	scan := bufio.NewScanner(input)
	for scan.Scan() {
		var cmd any
		if e = json.Unmarshal(scan.Bytes(), &cmd); e != nil {
			break
		}
		m.apply(cmd)
	}
	input.Close()
	if e != nil || scan.Err() != nil || m.err != nil {
		fmt.Fprintln(os.Stderr, e, scan.Err(), m.err)
		return 1
	}
	m.apply(map[string]any{"op": "pause", "paused": m.paused})
	m.paint()
	o := observedModel{inner: m, trace: trace, scenario: os.Getenv("NOCTURNE_TEST_SCENARIO"), setup: os.Getenv("NOCTURNE_TEST_SCENARIO") == "setup"}
	o.record("created")
	result, err := runModel(o)
	if result != nil {
		o = result.(observedModel)
		if err == nil {
			err = o.inner.err
		}
	}
	o.record("exit")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		return 1
	}
	return 0
}
func TestMain(m *testing.M) {
	if os.Getenv("NOCTURNE_TEST_SCENARIO") != "" {
		os.Exit(fixtureRun())
	}
	os.Exit(m.Run())
}
