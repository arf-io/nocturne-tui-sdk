package native
import ("bytes";"testing")
func TestTextRunClusterPersistenceAndOwnedResults(t *testing.T){
 s,e:=New(7);if e!=nil{t.Fatal(e)};defer s.Close()
 if _,e=s.Command(map[string]any{"op":"draft","text":"A é Z","emitWeather":false});e!=nil{t.Fatal(e)}
 old,e:=s.TextRunClusters(0,0);if e!=nil||len(old)!=5{t.Fatal(old,e)}
 if _,e=s.Command(map[string]any{"op":"draft","text":"A X é Z","emitWeather":false});e!=nil{t.Fatal(e)}
 rows,e:=s.TextRunClusters(0,0);if e!=nil||len(rows)!=7||rows[0][0]!=old[0][0]||rows[6][0]!=old[4][0]||rows[4][0]!=old[2][0]{t.Fatal(rows,e)}
 before,e:=s.Snapshot();if e!=nil{t.Fatal(e)};rows[0][0]=99;fresh,e:=s.TextRunClusters(0,0);if e!=nil||fresh[0][0]==99{t.Fatal(fresh,e)}
 after,e:=s.Snapshot();if e!=nil||!bytes.Equal(before,after){t.Fatal("query mutation",e)}
}
