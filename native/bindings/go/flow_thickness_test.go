package native
import ("bytes";"math";"testing")
func TestFlowThicknessOwnedGeometryAndReplay(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 for _,raw:=range []string{`{"op":"surface","id":1}`,`{"op":"ribbon","points":[[0,0,-2],[0,0,0]],"width":2,"surfaceId":1}`,`{"op":"flow","id":1,"flux":2,"stages":[{"name":"channel"}]}`,`{"op":"flow-surface","surfaceId":1,"flowId":1,"stage":"channel","referenceFlux":2}`,`{"op":"flow-thickness","surfaceId":1,"width":2,"speed":2,"maxDepth":1}`} {if _,e=s.CommandRaw([]byte(raw));e!=nil{t.Fatal(e)}}
 values,e:=s.FlowThickness(1);if e!=nil||len(values)!=6||math.Abs(values[1]-.5)>1e-11{t.Fatal(values,e)}
 rows,e:=s.SurfaceTriangles(1);if e!=nil||len(rows)!=12{t.Fatal(rows,e)}
 saved,e:=s.Snapshot();if e!=nil{t.Fatal(e)};rows[0][1]=99;fresh,e:=s.SurfaceTriangles(1);if e!=nil||fresh[0][1]==99{t.Fatal(fresh,e)}
 if e=s.AdvanceTo(500000);e!=nil{t.Fatal(e)};finish,e:=s.Snapshot();if e!=nil{t.Fatal(e)}
 if e=s.Restore(saved);e!=nil{t.Fatal(e)};if e=s.AdvanceTo(500000);e!=nil{t.Fatal(e)};replay,e:=s.Snapshot();if e!=nil||!bytes.Equal(finish,replay){t.Fatal("replay",e)}
}
