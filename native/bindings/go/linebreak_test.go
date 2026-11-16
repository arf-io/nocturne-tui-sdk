package native
import("testing";"reflect";"bytes";"strings")
func TestOwnedLineBreakReferences(t *testing.T){
 s,e:=New(2030);if e!=nil{t.Fatal(e)};defer s.Close();before,e:=s.Snapshot();if e!=nil{t.Fatal(e)}
 for _,test:=range []struct{source string;expected []uint32}{{"hello world",[]uint32{6,11}},{"A\r\nB",[]uint32{3,4}},{"",[]uint32{0}},{"你好",[]uint32{1,2}},{"1,234.5",[]uint32{7}},{"A\u2060B",[]uint32{3}},{"🇦🇧🇨🇩",[]uint32{2,4}},{"👩‍🚀",[]uint32{3}}}{
  row,e:=s.LineBreaks(test.source);if e!=nil||!reflect.DeepEqual(row,test.expected){t.Fatal(test.source,row,e)};row[0]=999;fresh,e:=s.LineBreaks(test.source);if e!=nil||!reflect.DeepEqual(fresh,test.expected){t.Fatal(fresh,e)}
 }
 if _,e=s.LineBreaks(string([]byte{0xff}));e==nil{t.Fatal("invalid UTF8 accepted")};if _,e=s.LineBreaks(strings.Repeat("A",2049));e==nil{t.Fatal("capacity accepted")}
 expected:=[][2]uint32{{2,0},{5,1},{7,1},{8,1}};details,e:=s.LineBreakDetails("A B\r\nC\u2028D");if e!=nil||!reflect.DeepEqual(details,expected){t.Fatal(details,e)};details[0][0]=999;fresh,e:=s.LineBreakDetails("A B\r\nC\u2028D");if e!=nil||!reflect.DeepEqual(fresh,expected){t.Fatal("details ownership",fresh,e)}
 empty,e:=s.LineBreakDetails("");if e!=nil||!reflect.DeepEqual(empty,[][2]uint32{{0,1}}){t.Fatal(empty,e)}
 if _,e=s.LineBreakDetails(string([]byte{0xff}));e==nil{t.Fatal("details invalid UTF8")};if _,e=s.LineBreakDetails(strings.Repeat("A",2049));e==nil{t.Fatal("details capacity")}
 after,e:=s.Snapshot();if e!=nil||!bytes.Equal(before,after){t.Fatal("query mutation",e)}
}
