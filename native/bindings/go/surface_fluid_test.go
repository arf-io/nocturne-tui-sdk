package native
import("testing";"math";"bytes")
func TestExplicitRotatingSurfaceFrameQueries(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 for _,command:=range []string{`{"op":"surface","id":1}`,`{"op":"mesh","triangles":[{"a":[10,20,30],"b":[14,20,30],"c":[10,20,34],"surfaceId":1}]}`,`{"op":"surface-fluid","surfaceId":1,"mass":3}`,`{"op":"surface-fluid-angular","surfaceId":1,"inertia":3,"pivot":[10,20,30],"orientation":[0,0,0.3826834323650898,0.9238795325112867],"omega":[0,0,1.5707963267948966]}`} {if _,e=s.CommandRaw([]byte(command));e!=nil{t.Fatal(e)}}
 before,e:=s.Snapshot();if e!=nil{t.Fatal(e)}
 rows,e:=s.SurfaceTriangles(1);if e!=nil||len(rows)!=1{t.Fatal(rows,e)}
 if math.Abs(rows[0][4]-(10+4*math.Sqrt(.5)))>1e-9{t.Fatal(rows)};rows[0][4]=999
 fresh,e:=s.SurfaceTriangles(1);if e!=nil||math.Abs(fresh[0][4]-(10+4*math.Sqrt(.5)))>1e-9{t.Fatal(fresh,e)}
 sample,e:=s.SurfaceWaveSample(1,11,31);if e!=nil{t.Fatal(e)}
 expected:=[6]float64{21,-math.Sqrt(.5),math.Sqrt(.5),0,math.Pi/2,0};for i,v:=range expected{if math.Abs(sample[i]-v)>1e-9{t.Fatal(sample,expected)}}
 after,e:=s.Snapshot();if e!=nil||!bytes.Equal(before,after){t.Fatal("query mutation",e)}
}
func TestAngularFluidOwnedLifecycle(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 if row,e:=s.SurfaceFluidAngular(1);e!=nil||row!=nil{t.Fatal(row,e)}
 for _,command:=range []string{`{"op":"surface","id":1}`,`{"op":"surface-fluid","surfaceId":1,"mass":3}`,`{"op":"surface-fluid-angular","surfaceId":1,"inertia":3,"omega":[1,2,3]}`} {if _,e=s.CommandRaw([]byte(command));e!=nil{t.Fatal(e)}}
 expected:=[12]float64{3,1,2,3,3,6,9,0,0,0,0,21};row,e:=s.SurfaceFluidAngular(1);if e!=nil||row==nil||*row!=expected{t.Fatal(row,e)}
 row[0]=999;fresh,e:=s.SurfaceFluidAngular(1);if e!=nil||fresh==nil||*fresh!=expected{t.Fatal(fresh,e)}
 if _,e=s.CommandRaw([]byte(`{"op":"export-surface-fluid","surfaceId":1}`));e!=nil{t.Fatal(e)}
 if _,e=s.CommandRaw([]byte(`{"op":"surface-fluid","surfaceId":1,"mass":5}`));e!=nil{t.Fatal(e)}
 if row,e=s.SurfaceFluidAngular(1);e!=nil||row!=nil{t.Fatal(row,e)}
 if _,e=s.SurfaceFluidAngular(0);e==nil{t.Fatal("invalid surface accepted")}
}
func TestSurfaceFluidOwnedRecord(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 for _,command:=range []string{`{"op":"surface","id":1}`,`{"op":"surface-fluid","surfaceId":1,"mass":3,"velocity":[1,2,3]}`} {if _,e=s.CommandRaw([]byte(command));e!=nil{t.Fatal(e)}}
 row,e:=s.SurfaceFluid(1);if e!=nil||row==nil{t.Fatal(row,e)};expected:=[15]float64{3,1,2,3,0,0,0,3,6,9,0,0,0,0,21};if *row!=expected{t.Fatal(row)}
 row[0]=999;fresh,e:=s.SurfaceFluid(1);if e!=nil||fresh==nil||*fresh!=expected{t.Fatal(fresh,e)}
 if _,e=s.SurfaceFluid(0);e==nil{t.Fatal("invalid id accepted")}
}
