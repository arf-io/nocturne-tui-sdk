package native
import("bytes";"math";"testing")
func TestColorFieldOwnedSampler(t *testing.T){
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 if _,err=s.CommandRaw([]byte(`{"op":"field","x":10,"y":5,"width":3,"speed":0,"strength":0.7,"continuous":true,"frequency":0,"phase":90}`));err!=nil{t.Fatal(err)}
 before,_:=s.Snapshot();row,err:=s.FieldSample(1,10,5);if err!=nil||row==nil||math.Abs(row[0]-.42)>2e-6||row[2]!=10||row[3]!=5{t.Fatal(row,err)}
 row[0]=-99;again,_:=s.FieldSample(1,10,5);if again[0]<0{t.Fatal("borrowed output")};after,_:=s.Snapshot();if !bytes.Equal(before,after){t.Fatal("query mutation")}
 if _,err=s.FieldSample(0,0,0);err==nil{t.Fatal("invalid ID accepted")};if _,err=s.FieldSample(1,math.NaN(),0);err==nil{t.Fatal("NaN accepted")};missing,err:=s.FieldSample(999,0,0);if err!=nil||missing!=nil{t.Fatal("missing",err)}
}
