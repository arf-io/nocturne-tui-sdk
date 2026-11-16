package native

import (
 "reflect"
 "strings"
 "testing"
)

func TestScriptRunsOwnedUnicodeScalarOffsets(t *testing.T) {
 s,err:=New(2030);if err!=nil {t.Fatal(err)};defer s.Close()
 expected:=[]ScriptRun{{0,3,"Latn"},{3,10,"Arab"}}
 rows,err:=s.ScriptRuns("a\u0301 العربية");if err!=nil||!reflect.DeepEqual(rows,expected){t.Fatal(rows,err)}
 if _,err=s.ScriptRuns("アー");err!=nil{t.Fatal(err)}
 if !reflect.DeepEqual(rows,expected){t.Fatal("query overwrote owned rows")}
 rows[0].Script="Zyyy"
 fresh,err:=s.ScriptRuns("a\u0301 العربية");if err!=nil||!reflect.DeepEqual(fresh,expected){t.Fatal(fresh,err)}
 emoji,err:=s.ScriptRuns("👩\u200d🔧");if err!=nil||!reflect.DeepEqual(emoji,[]ScriptRun{{0,3,"Zyyy"}}){t.Fatal(emoji,err)}
 empty,err:=s.ScriptRuns("");if err!=nil||len(empty)!=0{t.Fatal(empty,err)}
 for _,invalid:=range []string{string([]byte{0xff}),strings.Repeat("a",2049)} {if _,err=s.ScriptRuns(invalid);err==nil{t.Fatal("invalid source accepted")}}
 s.Close();if _,err=s.ScriptRuns("a");err==nil{t.Fatal("closed scene accepted")}
}
func TestBidiFontLinesPreserveParagraphBaseAndOwnership(t *testing.T) {
 s,err:=New(2030);if err!=nil{t.Fatal(err)};defer s.Close()
 rows,err:=s.BidiLines("אב ab ",[]uint32{3,6},2);if err!=nil{t.Fatal(err)}
 indices:=[]uint32{2,1,0,5,3,4};levels:=[]uint32{1,1,1,1,2,2}
 if len(rows)!=6{t.Fatal(rows)};for i,row:=range rows{if row[0]!=indices[i]||row[5]!=levels[i]{t.Fatal(rows)}}
 rows[0][0]=999;fresh,err:=s.BidiLines("אב ab ",[]uint32{3,6},2);if err!=nil||fresh[0][0]!=2{t.Fatal(fresh,err)}
 if _,err=s.BidiLines("a\u0301b",[]uint32{1,3},2);err==nil{t.Fatal("split grapheme accepted")}
 if _,err=s.BidiLines("a\nb",[]uint32{3},2);err==nil{t.Fatal("crossed hard break")}
}
