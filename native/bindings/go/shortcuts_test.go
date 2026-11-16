package native
import("reflect";"testing")
func TestShortcutNegotiation(t *testing.T){
 candidates:=[][3]uint32{{10,113,2},{10,115,2},{20,113,2},{30,120,8}};host:=[][3]uint32{{113,2,0},{115,2,0},{120,8,1}}
 rows,e:=NegotiateShortcuts([]uint32{10,20,30},candidates,host);want:=[][4]uint32{{10,115,2,1},{20,113,2,1},{30,0,0,0}};if e!=nil||!reflect.DeepEqual(rows,want){t.Fatal(rows,e)}
 rows[0][0]=99;if candidates[0][0]!=10{t.Fatal("borrowed result")}
 if _,e=NegotiateShortcuts([]uint32{1,1},nil,nil);e==nil{t.Fatal("duplicate actions accepted")}
 if empty,e:=NegotiateShortcuts(nil,nil,nil);e!=nil||len(empty)!=0{t.Fatal(empty,e)}
}
