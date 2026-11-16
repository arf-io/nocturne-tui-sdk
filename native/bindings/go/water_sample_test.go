package native
import("bytes";"math";"testing")
func TestWaterSampleOwnedBalance(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 for _,command:=range []string{`{"op":"surface","id":1}`,`{"op":"mesh","triangles":[{"a":[-2,0,-2],"b":[2,0,-2],"c":[0,0,2],"surfaceId":1}]}`,`{"op":"surface-water","surfaceId":1,"capacity":1}`,`{"op":"surface-water-add","triangleIndex":0,"volume":0.5}`} {if _,e=s.CommandRaw([]byte(command));e!=nil{t.Fatal(e)}}
 before,e:=s.Snapshot();if e!=nil{t.Fatal(e)};row,e:=s.WaterSample(0);if e!=nil||row==nil{t.Fatal(row,e)}
 for i,v:=range [8]float64{1,.5,.5,.5,0,0,0,1}{if math.Abs(row[i]-v)>1e-8{t.Fatal(row)}}
 row[2]=999;fresh,e:=s.WaterSample(0);if e!=nil||math.Abs(fresh[2]-.5)>1e-8{t.Fatal(fresh,e)};after,e:=s.Snapshot();if e!=nil||!bytes.Equal(before,after){t.Fatal("mutation",e)}
}
