package native

import (
	"encoding/json"
	"testing"
)

func TestNativeFlowTransport(t *testing.T) {
	s, e := New(17)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	if _, e = s.CommandRaw([]byte(`{"op":"flow","id":1,"flux":2,"stages":[{"name":"channel","delayUs":500000},{"name":"sheet","delayUs":250000}]}`)); e != nil {
		t.Fatal(e)
	}
	if e = s.AdvanceTo(1000000); e != nil {
		t.Fatal(e)
	}
	data, e := s.Info()
	if e != nil {
		t.Fatal(e)
	}
	var v struct {
		Flows []struct{ InjectedVolume, DeliveredVolume, StoredVolume float64 }
	}
	if e = json.Unmarshal(data, &v); e != nil {
		t.Fatal(e)
	}
	if len(v.Flows) != 1 || v.Flows[0].InjectedVolume != 2 || v.Flows[0].DeliveredVolume != .5 || v.Flows[0].StoredVolume != 1.5 {
		t.Fatal(string(data))
	}
}
