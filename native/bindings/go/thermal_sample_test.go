package native
import("bytes";"math";"testing")
func TestThermalSampleOwnedAnalyticEnergy(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 if _,e=s.CommandRaw([]byte(`{"op":"mesh","triangles":[{"a":[-2,-2,0],"b":[2,-2,0],"c":[0,2,0]}]}`));e!=nil{t.Fatal(e)}
 row,e:=s.ThermalSample(0);if e!=nil||row!=nil{t.Fatal(row,e)}
 if _,e=s.CommandRaw([]byte(`{"op":"surface-thermal","triangleIndex":0,"temperature":293,"capacity":2,"power":4}`));e!=nil{t.Fatal(e)}
 if e=s.AdvanceTo(500000);e!=nil{t.Fatal(e)};before,e:=s.Snapshot();if e!=nil{t.Fatal(e)}
 row,e=s.ThermalSample(0);if e!=nil||row==nil{t.Fatal(row,e)}
 for i,v:=range [10]float64{294,588,586,2,0,0,0,2,4,293}{if math.Abs(row[i]-v)>1e-6{t.Fatal(row)}}
 row[0]=999;fresh,e:=s.ThermalSample(0);if e!=nil||math.Abs(fresh[0]-294)>1e-6{t.Fatal(fresh,e)}
 after,e:=s.Snapshot();if e!=nil||!bytes.Equal(before,after){t.Fatal("query changed scene",e)}
 if _,e=s.ThermalSample(1);e==nil{t.Fatal("missing triangle accepted")}
}
