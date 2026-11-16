package native

import "testing"

func TestSelectedSource(t *testing.T) {
	s, e := New(2030)
	if e != nil {
		t.Fatal(e)
	}
	defer s.Close()
	s.CommandRaw([]byte(`{"op":"draft","text":"Aé日本Z","emitWeather":false}`))
	s.CommandRaw([]byte(`{"op":"select","anchor":5,"caret":1}`))
	text, e := s.SelectedText()
	if e != nil || text != "é日本" {
		t.Fatal(text, e)
	}
}
