package native
import("testing";"math")
func TestHullImmersionAnalyticOwned(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 vertices:=[][3]float64{{0,0,0},{1,0,0},{0,1,0},{0,0,1}};faces:=[][3]uint32{{0,2,1},{0,1,3},{0,3,2},{1,2,3}}
 row,e:=s.HullImmersion(vertices,faces,.5);if e!=nil{t.Fatal(e)};expected:=[5]float64{1.0/6,7.0/48,15.0/56,11.0/56,15.0/56}
 for i,x:=range row{if math.Abs(x-expected[i])>1e-9{t.Fatal(row)}}
 row[0]=999;fresh,e:=s.HullImmersion(vertices,faces,.5);if e!=nil||math.Abs(fresh[0]-1.0/6)>1e-9{t.Fatal(fresh,e)}
 if _,e=s.HullImmersion(vertices,faces,math.NaN());e==nil{t.Fatal("nonfinite plane accepted")}
 if _,e=s.HullImmersion(vertices,faces[:3],.5);e==nil{t.Fatal("open hull accepted")}
}
func TestOrientedHullImmersionAndWrenchOwned(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 vertices:=[][3]float64{{0,0,0},{1,0,0},{0,1,0},{0,0,1}};faces:=[][3]uint32{{0,2,1},{0,1,3},{0,3,2},{1,2,3}}
 expected:=[5]float64{1.0/6,7.0/48,15.0/56,11.0/56,15.0/56}
 row,e:=s.HullImmersionPlane(vertices,faces,[3]float64{0,.5,0},[3]float64{0,10,0});if e!=nil{t.Fatal(e)}
 for i,value:=range row{if math.Abs(value-expected[i])>1e-9{t.Fatal(row)}}
 row[1]=999;fresh,e:=s.HullImmersionPlane(vertices,faces,[3]float64{0,.5,0},[3]float64{0,1,0});if e!=nil||math.Abs(fresh[1]-7.0/48)>1e-9{t.Fatal(fresh,e)}
 wrench,e:=s.HullBuoyancyPlane(vertices,faces,[3]float64{0,.5,0},[3]float64{0,1,0},48,1,7,[3]float64{});if e!=nil{t.Fatal(e)}
 target:=[11]float64{1.0/6,7.0/48,15.0/56,11.0/56,15.0/56,0,0,0,-15.0/8,0,15.0/8};for i,value:=range wrench{if math.Abs(value-target[i])>1e-9{t.Fatal(wrench)}}
 if _,e=s.HullImmersionPlane(vertices,faces,[3]float64{},[3]float64{});e==nil{t.Fatal("zero normal accepted")}
}
func TestRetainedHullPoseOwned(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 for _,command:=range []string{`{"op":"surface","id":1}`,`{"op":"float-body","id":1,"surfaceId":1}`,`{"op":"float-hull","id":1,"vertices":[[0,0,0],[1,0,0],[0,1,0],[0,0,1]],"faces":[[0,2,1],[0,1,3],[0,3,2],[1,2,3]],"inertia":[1,2,3]}`} {if _,e=s.CommandRaw([]byte(command));e!=nil{t.Fatal(e)}}
 row,e:=s.FloatHull(1);if e!=nil||row==nil{t.Fatal(row,e)};if math.Abs(row[13]-1.0/6)>1e-9||row[3]!=1||row[7]!=1||row[8]!=2||row[9]!=3{t.Fatal(row)}
 row[13]=999;fresh,e:=s.FloatHull(1);if e!=nil||fresh==nil||math.Abs(fresh[13]-1.0/6)>1e-9{t.Fatal(fresh,e)}
 if _,e=s.CommandRaw([]byte(`{"op":"remove-float-body","id":1}`));e!=nil{t.Fatal(e)};row,e=s.FloatHull(1);if e!=nil||row!=nil{t.Fatal(row,e)}
}
func TestHullMeshImmersionIndependentTetrahedron(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 vertices:=[][3]float64{{0,0,0},{1,0,0},{0,1,0},{0,0,1}};faces:=[][3]uint32{{0,2,1},{0,1,3},{0,3,2},{1,2,3}};water:=[][9]float64{{-2,.5,-2,4,.5,-2,-2,.5,4}}
 row,e:=s.HullMeshImmersion(vertices,faces,water);if e!=nil{t.Fatal(e)};expected:=[5]float64{1.0/6,7.0/48,15.0/56,11.0/56,15.0/56};for i,x:=range row{if math.Abs(x-expected[i])>1e-9{t.Fatal(row)}}
 row[1]=999;fresh,e:=s.HullMeshImmersion(vertices,faces,water);if e!=nil||math.Abs(fresh[1]-7.0/48)>1e-9{t.Fatal(fresh,e)}
 if _,e=s.HullMeshImmersion(vertices,faces,append(water,water...));e==nil{t.Fatal("overlapping water accepted")}
}
