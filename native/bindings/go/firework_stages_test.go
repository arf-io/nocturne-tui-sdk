package native
import("bytes";"encoding/json";"testing")
func TestFireworkStageOwnedReadback(t *testing.T){
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 _,err=s.CommandRaw([]byte(`{"op":"emitter","id":1,"effect":"weather/chrysanthemum","seed":73,"count":1,"runningTimeMs":0,"coreMs":200}`));if err!=nil{t.Fatal(err)}
 if err=s.AdvanceTo(8333);err!=nil{t.Fatal(err)};before,_:=s.Snapshot();raw,err:=s.InfoComplete();if err!=nil{t.Fatal(err)}
 var q struct{Emitters []struct{BurstStages struct{SampleLimit int;Samples [][]float64}}}
 if err=json.Unmarshal(raw,&q);err!=nil{t.Fatal(err)}
 if len(q.Emitters)!=1||q.Emitters[0].BurstStages.SampleLimit!=16||len(q.Emitters[0].BurstStages.Samples)!=1||q.Emitters[0].BurstStages.Samples[0][3]!=1{t.Fatal(q)}
 raw[0]=0;again,err:=s.InfoComplete();if err!=nil||!json.Valid(again){t.Fatal("borrowed stage metadata",err)};after,_:=s.Snapshot();if !bytes.Equal(before,after){t.Fatal("stage query changed source")}
}
