package native

import("bytes";"encoding/json";"testing")
func TestGraphMetadataOwnedReadback(t *testing.T){
 s,err:=New(42);if err!=nil {t.Fatal(err)};defer s.Close()
 for _,c:=range []string{`{"op":"node","id":1,"pinned":true,"position":[1,2,3]}`,`{"op":"node","id":2}`,`{"op":"edge","from":1,"to":2,"kind":"depends"}`} {if _,err=s.CommandRaw([]byte(c));err!=nil {t.Fatal(err)}}
 before,_:=s.Snapshot();raw,err:=s.InfoComplete();if err!=nil {t.Fatal(err)}
 var info struct{Graph struct{Dimensions int;LayoutMode string;Edges []struct{From,To int;Kind string}};Nodes []struct{Pinned bool;TargetPosition []float64}}
 if err=json.Unmarshal(raw,&info);err!=nil {t.Fatal(err)}
 if info.Graph.Dimensions!=3||info.Graph.LayoutMode!="layered"||len(info.Graph.Edges)!=1||info.Graph.Edges[0].Kind!="depends"||!info.Nodes[0].Pinned||info.Nodes[0].TargetPosition[0]!=1 {t.Fatal(info)}
 raw[0]=0;again,err:=s.InfoComplete();if err!=nil||!json.Valid(again){t.Fatal("borrowed metadata",err)}
 after,_:=s.Snapshot();if !bytes.Equal(before,after){t.Fatal("metadata mutation")}
}
