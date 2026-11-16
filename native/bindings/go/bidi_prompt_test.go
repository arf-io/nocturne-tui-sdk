package native

import (
 "bytes"
 "testing"
)

func TestBidiPromptOwnedConsumer(t *testing.T) {
 s,err:=New(42);if err!=nil {t.Fatal(err)};defer s.Close()
 for _,command:=range []string{
  `{"op":"prompt","layout":"bidi","direction":"auto","mode":"grow"}`,
  `{"op":"draft","text":"א́ב","emitWeather":false}`,
 } {if _,err=s.CommandRaw([]byte(command));err!=nil {t.Fatal(err)}}
 before,_:=s.Snapshot();rows,err:=s.PromptVisualLayout()
 if err!=nil||len(rows)!=2 {t.Fatal(rows,err)}
 if rows[0][0]!=2||rows[1][0]!=0||rows[1][1]!=2||rows[1][8]!=1 {t.Fatal(rows)}
 rows[0][0]=999;again,err:=s.PromptVisualLayout()
 if err!=nil||again[0][0]!=2 {t.Fatal("borrowed visual rows",err)}
 after,_:=s.Snapshot();if !bytes.Equal(before,after) {t.Fatal("query mutated state")}
 if _,err=s.CommandRaw([]byte(`{"op":"prompt","direction":"invalid"}`));err==nil {t.Fatal("invalid direction accepted")}
 after,_=s.Snapshot();if !bytes.Equal(before,after) {t.Fatal("rejection mutated state")}
}
