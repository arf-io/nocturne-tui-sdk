package native

import (
	"bytes"
	"encoding/json"
	"fmt"
	"testing"
)

func TestResourceAnimationBindingsMatchPublicAuthoring(t *testing.T) {
	for family, fields := range map[string]map[string]float64{"emitter": {"glitterHz": 30, "glitterDepth": .2, "coreAlpha": .3, "residualMs": 350.125, "residualAlpha": .4}, "electrical-arc": {"speed": 20, "jitter": .5, "alpha": .4, "flicker": .2, "delayMs": 50.125, "holdMs": 150.125, "fadeMs": 250.125, "repeatMs": 3000.125}} {
		for field, value := range fields {
			t.Run(family+"/"+field, func(t *testing.T) {
				s, e := New(42)
				if e != nil {
					t.Fatal(e)
				}
				defer s.Close()
				o, e := New(42)
				if e != nil {
					t.Fatal(e)
				}
				defer o.Close()
				cmd := func(s *Scene, text string) {
					if _, e := s.CommandRaw([]byte(text)); e != nil {
						t.Fatal(e)
					}
				}
				id := 7
				base := `{"op":"electrical-arc","id":7,"points":[{"position":[0,0,0],"parent":-1},{"position":[3,0,0],"parent":0}]}`
				if family == "emitter" {
					id = 1
					base = `{"op":"emitter","id":1,"effect":"weather/chrysanthemum","seed":73,"count":8,"runningTimeMs":0,"lifetimeMinMs":2000,"lifetimeMaxMs":2000}`
				}
				cmd(s, base)
				var public map[string]interface{}
				json.Unmarshal([]byte(base), &public)
				if family == "electrical-arc" {
					public[field] = value
				}
				raw, _ := json.Marshal(public)
				cmd(o, string(raw))
				if family == "emitter" {
					if e = s.AdvanceTo(250000); e != nil {
						t.Fatal(e)
					}
					if e = o.AdvanceTo(250000); e != nil {
						t.Fatal(e)
					}
					cmd(o, fmt.Sprintf(`{"op":"burst-style","id":1,"%s":%g}`, field, value))
				}
				cmd(s, fmt.Sprintf(`{"op":"define","path":"/control","value":%g,"binding":{"family":"%s","id":%d,"field":"%s"}}`, value, family, id, field))
				cmd(s, `{"op":"remove-value","path":"/control"}`)
				a, e := s.Snapshot()
				if e != nil {
					t.Fatal(e)
				}
				b, e := o.Snapshot()
				if e != nil {
					t.Fatal(e)
				}
				if !bytes.Equal(a, b) {
					t.Fatal("binding differs from public authoring")
				}
				if _, e = s.CommandRaw([]byte(fmt.Sprintf(`{"op":"define","path":"/bad","value":-1,"binding":{"family":"%s","id":%d,"field":"%s"}}`, family, id, field))); e == nil {
					t.Fatal("invalid control accepted")
				}
				after, e := s.Snapshot()
				if e != nil || !bytes.Equal(a, after) {
					t.Fatal("rejection mutated source", e)
				}
			})
		}
	}
}
