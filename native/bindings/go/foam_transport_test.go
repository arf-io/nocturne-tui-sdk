package native
import ("bytes";"math";"testing")
func TestFoamTransportOwnedFluxReplay(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close()
 for _,command:=range []string{
`{"op":"floor","enabled":false}`,
`{"op":"surface","id":1,"restitution":1,"friction":0,"settleSpeed":0}`,
`{"op":"mesh","triangles":[{"a":[0,0,0],"b":[1,0,0],"c":[0,0,1],"surfaceId":1},{"a":[1,0,0],"b":[1,0,1],"c":[0,0,1],"surfaceId":1}]}`,
`{"op":"surface-foam","surfaceId":1,"sourceRate":0,"decay":0,"impactGain":0.001}`,
`{"op":"emitter","id":1,"effect":"weather/autumn-drift","count":1,"runningTimeMs":0,"shape":"point","position":[0.2,1,0.2],"velocity":[0,-240,0],"extent":[0,0,0],"spread":[0,0,0],"gravity":[0,0,0],"wind":[0,0,0],"windVariation":[0,0,0],"drag":0,"lift":0,"flutterHz":0,"flutterAmount":0,"tumble":[0,0,0],"deposit":false,"collision":true,"lifetimeMinMs":10000,"lifetimeMaxMs":10000,"sizeMin":1,"sizeMax":1,"colliders":{"surfaces":[1]}}`,
}{if _,e=s.CommandRaw([]byte(command));e!=nil{t.Fatal(e)}}
 if e=s.AdvanceTo(8333);e!=nil{t.Fatal(e)}
 if _,e=s.Command(map[string]any{"op":"surface-foam-transport","surfaceId":1,"velocity":[]float64{1,0}});e!=nil{t.Fatal(e)}
 saved,e:=s.Snapshot();if e!=nil{t.Fatal(e)};if e=s.AdvanceTo(16666);e!=nil{t.Fatal(e)}
 rows,e:=s.SurfaceFoamTransport(1);if e!=nil||len(rows)!=2{t.Fatal(rows,e)}
 amount:=.24*2/120;if math.Abs(rows[0][1]-(.24-amount))>1e-11||math.Abs(rows[1][1]-amount)>1e-11{t.Fatal(rows)}
 for _,r:=range rows{if math.Abs(r[2]+r[5]-r[1]-r[3]-r[4]-r[6])>1e-11{t.Fatal(r)}}
 finish,e:=s.Snapshot();if e!=nil{t.Fatal(e)};rows[0][1]=99
 fresh,e:=s.SurfaceFoamTransport(1);if e!=nil||fresh[0][1]==99{t.Fatal(fresh,e)}
 if e=s.Restore(saved);e!=nil{t.Fatal(e)};if e=s.AdvanceTo(16666);e!=nil{t.Fatal(e)}
 replay,e:=s.Snapshot();if e!=nil||!bytes.Equal(finish,replay){t.Fatal("replay",e)}
}
