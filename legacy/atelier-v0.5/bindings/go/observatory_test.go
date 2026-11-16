package nocturne

import (
	"encoding/csv"
	"os"
	"strconv"
	"testing"
)

func TestObservatoryColorCorpus(t *testing.T) {
	f, e := os.Open("../../tests/observatory/color-fixtures.csv")
	if e != nil {
		t.Fatal(e)
	}
	defer f.Close()
	rows, e := csv.NewReader(f).ReadAll()
	if e != nil {
		t.Fatal(e)
	}
	for _, r := range rows[1:] {
		var v [5]int64
		for i, x := range r {
			v[i], e = strconv.ParseInt(x, 10, 64)
			if e != nil {
				t.Fatal(e)
			}
		}
		c, e := OklchColor(int32(v[0]), int32(v[1]), int32(v[2]))
		if e != nil || c != uint32(v[3]) {
			t.Fatalf("color %v: %v %v", r, c, e)
		}
		l, e := OklchLightness(c)
		if e != nil || l != int32(v[4]) {
			t.Fatalf("lightness %v", r)
		}
	}
}
func TestObservatoryRejectsInvalid(t *testing.T) {
	if _, e := OklchColor(-1, 0, 0); e == nil {
		t.Fatal("negative L accepted")
	}
	if _, e := OklchColor(700, 4001, 0); e == nil {
		t.Fatal("bad C")
	}
	if _, e := OklchLightness(0x1000000); e == nil {
		t.Fatal("bad RGB")
	}
}
