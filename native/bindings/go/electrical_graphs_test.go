package native
import("bytes";"encoding/json";"testing")
func TestElectricalGraphOwnedGeometry(t *testing.T){
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 _,err=s.CommandRaw([]byte(`{"op":"electrical-arc","id":7,"points":[{"position":[0,0,0],"parent":-1},{"position":[3,0,0],"parent":0}],"speed":10,"holdMs":200,"fadeMs":300,"jitter":0,"flicker":0}`));if err!=nil{t.Fatal(err)}
 if err=s.AdvanceTo(200000);err!=nil{t.Fatal(err)};before,_:=s.Snapshot();raw,err:=s.InfoComplete();if err!=nil{t.Fatal(err)}
 var q struct{ElectricalArcs []struct{Phase string;Segments [][]float64}}
 if err=json.Unmarshal(raw,&q);err!=nil{t.Fatal(err)}
 if len(q.ElectricalArcs)!=1||q.ElectricalArcs[0].Phase!="leader"||len(q.ElectricalArcs[0].Segments)!=1||q.ElectricalArcs[0].Segments[0][3]!=2{t.Fatal(q)}
 raw[0]=0;again,err:=s.InfoComplete();if err!=nil||!json.Valid(again){t.Fatal("borrowed arc metadata",err)};after,_:=s.Snapshot();if !bytes.Equal(before,after){t.Fatal("query mutated source")}
}
