package native

import (
 "bytes"
 "encoding/json"
 "encoding/binary"
 "math"
 "testing"
)

func TestGeneralAPIBatchRuntimeContract(t *testing.T) {
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 saved,err:=s.Snapshot();if err!=nil{t.Fatal(err)};raw,err:=s.Info();if err!=nil{t.Fatal(err)}
 var info struct{Contract struct{ABIVersion uint32 `json:"abiVersion"`;SnapshotSchema uint32 `json:"snapshotSchema"`;SourceSchema uint32 `json:"sourceSchema"`;SnapshotCapacityBytes uint32 `json:"snapshotCapacityBytes"`;MetadataProfile string `json:"metadataProfile"`;CommandProfile string `json:"commandProfile"`;BindingFamilies []string `json:"bindingFamilies"`;Features []string `json:"features"`} `json:"contract"`}
 if err=json.Unmarshal(raw,&info);err!=nil{t.Fatal(err)};c:=info.Contract
 if c.ABIVersion!=binary.LittleEndian.Uint32(saved[8:])||c.SnapshotSchema!=binary.LittleEndian.Uint32(saved[12:])||c.SourceSchema!=binary.LittleEndian.Uint32(saved[28:])||c.SnapshotCapacityBytes!=uint32(len(saved)){t.Fatal("runtime contract disagrees with wire writer")}
 if c.MetadataProfile!="nocturne.metadata/v1"||c.CommandProfile!="nocturne.commands/v1"||len(c.BindingFamilies)!=24{t.Fatal("runtime discovery profile")}
 families:=map[string]bool{};for _,family:=range c.BindingFamilies{if families[family]{t.Fatal("duplicate binding family",family)};families[family]=true}
 if !families["electrical-arc"]{t.Fatal("missing electrical arc binding")}
 if !families["accessibility"]{t.Fatal("missing accessibility binding")}
 after,err:=s.Snapshot();if err!=nil||!bytes.Equal(saved,after){t.Fatal("discovery mutated source",err)}
 if err=s.Restore(saved);err!=nil{t.Fatal(err)};restored,err:=s.Info();if err!=nil||!bytes.Equal(raw,restored){t.Fatal("restored discovery",err)}
}

func TestGeneralAPIBatchWidgetMetadata(t *testing.T) {
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 if _,err=s.CommandRaw([]byte(`{"op":"widget","id":1,"kind":"donut","width":2000000000,"height":1000000000,"alpha":0.75,"enabled":false,"selected":true,"data":[1,2,4]}`));err!=nil{t.Fatal(err)}
 saved,err:=s.Snapshot();if err!=nil{t.Fatal(err)}
 raw,err:=s.Info();if err!=nil{t.Fatal(err)}
 var info struct{Widgets []struct{Width int64 `json:"width"`;Height int64 `json:"height"`;Alpha float64 `json:"alpha"`;Enabled bool `json:"enabled"`;Selected bool `json:"selected"`;Data []float64 `json:"data"`} `json:"widgets"`}
 if err=json.Unmarshal(raw,&info);err!=nil{t.Fatal(err)}
 if len(info.Widgets)!=1{t.Fatal("missing widget metadata")};w:=info.Widgets[0]
 if w.Width!=2000000000||w.Height!=1000000000||w.Alpha!=.75||w.Enabled||!w.Selected||len(w.Data)!=3||w.Data[2]!=4{t.Fatal("authored widget properties",w)}
 after,err:=s.Snapshot();if err!=nil||!bytes.Equal(saved,after){t.Fatal("metadata mutated source",err)}
 if err=s.Restore(saved);err!=nil{t.Fatal(err)};restored,err:=s.Info();if err!=nil||!bytes.Equal(raw,restored){t.Fatal("restored metadata",err)}
 if _,err=s.CommandRaw([]byte(`{"op":"widget","id":1,"data":[9]}`));err!=nil{t.Fatal(err)}
 if info.Widgets[0].Data[2]!=4{t.Fatal("metadata array was borrowed")}
}

func TestGeneralAPIBatchPanelMetadata(t *testing.T) {
 for _,row:=range []struct{name,command,binding string;expected []string}{
  {"window",`{"op":"window","id":1,"width":2000000000,"height":1000000000,"title":"NOC 日本","durationMs":1200}`,`{"op":"define","path":"/width","value":1234,"binding":{"family":"window","id":1,"field":"width"}}`,[]string{`"width":2000000000`,`"height":1000000000`,`"title":"NOC 日本"`,`"durationUs":1200000`}},
  {"area",`{"op":"area","id":1,"width":2147483647,"height":2147483647,"layout":"queue","hideEmpty":true,"fadeMs":500}`,`{"op":"define","path":"/width","value":1234,"binding":{"family":"area","id":1,"field":"width"}}`,[]string{`"width":2147483647`,`"height":2147483647`,`"layout":"queue"`,`"hideEmpty":true`,`"fadeUs":500000`}},
 }{t.Run(row.name,func(t *testing.T){
  s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
  if _,err=s.CommandRaw([]byte(row.command));err!=nil{t.Fatal(err)}
  saved,err:=s.Snapshot();if err!=nil{t.Fatal(err)};raw,err:=s.Info();if err!=nil{t.Fatal(err)}
  for _,expected:=range row.expected{if !bytes.Contains(raw,[]byte(expected)){t.Fatal("missing authored panel metadata",expected)}}
  after,err:=s.Snapshot();if err!=nil||!bytes.Equal(saved,after){t.Fatal("metadata mutated source",err)}
  if err=s.Restore(saved);err!=nil{t.Fatal(err)};restored,err:=s.Info();if err!=nil||!bytes.Equal(raw,restored){t.Fatal("restored panel metadata",err)}
  if _,err=s.CommandRaw([]byte(row.binding));err!=nil{t.Fatal(err)}
  if _,err=s.CommandRaw([]byte(`{"op":"remove-value","path":"/width"}`));err!=nil{t.Fatal(err)}
  changed,err:=s.Info();if err!=nil||!bytes.Contains(changed,[]byte(`"width":1234`)){t.Fatal("binding teardown lost authored width",err)}
  if !bytes.Contains(raw,[]byte(row.expected[0])){t.Fatal("metadata query was borrowed")}
 })}
}

func TestGeneralAPIBatchAccessibilityBinding(t *testing.T) {
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 for _,command:=range []string{
  `{"op":"define","path":"/motion","value":true,"binding":{"family":"accessibility","field":"reducedMotion"}}`,
  `{"op":"bind","path":"/motion","binding":{"family":"accessibility","field":"screenReader"}}`,
  `{"op":"set","path":"/motion","value":false}`,
 }{if _,err=s.CommandRaw([]byte(command));err!=nil{t.Fatal(err)}}
 raw,err:=s.Info();if err!=nil{t.Fatal(err)}
 var info struct{Accessibility struct{ReducedMotion bool `json:"reducedMotion"`;ScreenReader bool `json:"screenReader"`} `json:"accessibility"`}
 if err=json.Unmarshal(raw,&info);err!=nil||!info.Accessibility.ReducedMotion||info.Accessibility.ScreenReader{t.Fatal("preference ownership",err)}
 saved,err:=s.Snapshot();if err!=nil{t.Fatal(err)}
 if _,err=s.CommandRaw([]byte(`{"op":"set","path":"/motion","value":1}`));err==nil{t.Fatal("boolean coercion")}
 after,err:=s.Snapshot();if err!=nil||!bytes.Equal(saved,after){t.Fatal("rejected coercion changed source",err)}
 if err=s.Restore(saved);err!=nil{t.Fatal(err)}
}

func TestGeneralAPIBatchCharacterRules(t *testing.T) {
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 baseline,err:=s.Render();if err!=nil{t.Fatal(err)}
 expected:=append([]byte(nil),baseline.Bytes...)
 for x:=2;x<6;x++{offset:=(2*int(baseline.Width)+x)*16+4;binary.LittleEndian.PutUint32(expected[offset:],binary.LittleEndian.Uint32(expected[offset:])^0xffffff)}
 if _,err=s.CommandRaw([]byte(`{"op":"character-rule","rule":{"id":"invert","selector":{"rect":{"x":2,"y":2,"width":4,"height":1}},"compositeSpace":"srgb","foregroundEffects":[{"type":"invert"}]}}`));err!=nil{t.Fatal(err)}
 saved,err:=s.Snapshot();if err!=nil{t.Fatal(err)}
 painted,err:=s.Render();if err!=nil||!bytes.Equal(painted.Bytes,expected){t.Fatal("independent character oracle",err)}
 pure,err:=s.Snapshot();if err!=nil||!bytes.Equal(saved,pure){t.Fatal("render mutated state",err)}
 if _,err=s.CommandRaw([]byte(`{"op":"remove-character-rule","id":"invert"}`));err!=nil{t.Fatal(err)}
 if err=s.Restore(saved);err!=nil{t.Fatal(err)}
 painted,err=s.Render();if err!=nil||!bytes.Equal(painted.Bytes,expected){t.Fatal("restored rule cache",err)}
 raw,err:=s.Info();if err!=nil{t.Fatal(err)}
 var info struct{Rules []struct{ID string `json:"id"`} `json:"characterRules"`}
 if err=json.Unmarshal(raw,&info);err!=nil||len(info.Rules)!=1||info.Rules[0].ID!="invert"{t.Fatal("rule metadata",err)}
}
func TestGeneralAPIBatchCompositeSpaces(t *testing.T) {
 for space,expected:=range []uint32{0x808080,0xbcbcbc,0x636363,0x636363}{
  out,err:=CompositeInSpace(0,0xffffff,65535,32768,0,0,0,uint32(space));if err!=nil||out!=([2]uint32{expected,65535}){t.Fatal("space midpoint",space,out,err)}
  out,err=CompositeInSpace(0x123456,0xabcdef,65535,0,0,0,0,uint32(space));if err!=nil||out!=([2]uint32{0x123456,65535}){t.Fatal("space endpoint",space,out,err)}
 }
 if _,err:=CompositeInSpace(0,0,65535,65535,0,0,0,4);err==nil{t.Fatal("accepted invalid space")}
}
func TestGeneralAPIBatchExplicitRegion(t *testing.T) {
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 baseline,err:=s.Render();if err!=nil{t.Fatal(err)};expected:=append([]byte(nil),baseline.Bytes...)
 binary.LittleEndian.PutUint32(expected[4:],binary.LittleEndian.Uint32(expected[4:])^0xffffff)
 for _,command:=range []string{
  `{"op":"character-region","region":{"id":"fragment","path":"/app/fragment","state":"selected","cells":[0],"indices":[9]}}`,
  `{"op":"character-rule","rule":{"id":"fragment-paint","selector":{"path":"/app/fragment","indices":[9]},"states":{"selected":{"foregroundEffects":[{"type":"invert"}]}}}}`,
 }{if _,err=s.CommandRaw([]byte(command));err!=nil{t.Fatal(err)}}
 if _,err=s.InspectCharacterCell(0,0);err==nil{t.Fatal("inspected stale command frame")}
 saved,err:=s.Snapshot();if err!=nil{t.Fatal(err)};frame,err:=s.Render();if err!=nil||!bytes.Equal(frame.Bytes,expected){t.Fatal("explicit region oracle",err)}
 inspected,err:=s.InspectCharacterCell(0,0);if err!=nil||inspected.Path!="/app/fragment"||inspected.State!="selected"||inspected.Index!=9{t.Fatal("owner inspection",inspected,err)}
 pure,err:=s.Snapshot();if err!=nil||!bytes.Equal(saved,pure){t.Fatal("inspection mutated state",err)}
 if _,err=s.CommandRaw([]byte(`{"op":"remove-character-region","id":"fragment"}`));err!=nil{t.Fatal(err)}
 if err=s.Restore(saved);err!=nil{t.Fatal(err)}
 if _,err=s.InspectCharacterCell(0,0);err==nil{t.Fatal("inspected stale restored frame")}
 frame,err=s.Render();if err!=nil||!bytes.Equal(frame.Bytes,expected){t.Fatal("region restore",err)}
 restored,err:=s.InspectCharacterCell(0,0);if err!=nil||restored!=inspected{t.Fatal("restored inspection differs",err)}
}

func TestGeneralAPIBatchRetainedTransformsAndReplay(t *testing.T) {
 s, err := New(42)
 if err != nil { t.Fatal(err) }; defer s.Close()
 command := func(text string) { t.Helper(); if _, err := s.CommandRaw([]byte(text)); err != nil { t.Fatal(err) } }
 for _, text := range []string{
  `{"op":"define","path":"/go","value":0}`,
  `{"op":"define","path":"/seconds","value":2}`,
  `{"op":"define","path":"/milliseconds","value":0}`,
  `{"op":"trigger","id":1,"source":"/go","target":"/milliseconds","debounceMs":500,"expression":{"convert":{"value":{"path":"/seconds"},"from":"seconds","to":"milliseconds"}}}`,
  `{"op":"set","path":"/go","value":1}`,
  `{"op":"set","path":"/seconds","value":3}`,
 } { command(text) }
 before, err := s.Snapshot(); if err != nil { t.Fatal(err) }
 if _, err = s.CommandRaw([]byte(`{"op":"remove-value","path":"/seconds"}`)); err == nil { t.Fatal("removed compiled source") }
 after, err := s.Snapshot(); if err != nil || !bytes.Equal(before, after) { t.Fatal("failed removal mutated state", err) }
 if err = s.AdvanceTo(500000); err != nil { t.Fatal(err) }
 raw, err := s.Info(); if err != nil { t.Fatal(err) }
 var info struct { Values map[string]float64 `json:"values"` }
 if err = json.Unmarshal(raw, &info); err != nil || info.Values["/milliseconds"] != 3000 { t.Fatal("execution-time conversion", err) }
 finish, err := s.Snapshot(); if err != nil { t.Fatal(err) }
 if _, err = s.Render(); err != nil { t.Fatal(err) }
 pure, err := s.Snapshot(); if err != nil || !bytes.Equal(finish, pure) { t.Fatal("render mutated state", err) }
 if err = s.Restore(before); err != nil { t.Fatal(err) }
 if err = s.AdvanceTo(500000); err != nil { t.Fatal(err) }
 replay, err := s.Snapshot(); if err != nil || !bytes.Equal(finish, replay) { t.Fatal("replay differs", err) }
}

func TestGeneralAPIBatchGraphBindingOracle(t *testing.T) {
 s, err := New(42); if err != nil { t.Fatal(err) }; defer s.Close()
 oracle, err := New(42); if err != nil { t.Fatal(err) }; defer oracle.Close()
 for _, scene := range []*Scene{s, oracle} {
  if _, err = scene.CommandRaw([]byte(`{"op":"node","id":1,"label":"SDK graph card","position":[0,6,0]}`)); err != nil { t.Fatal(err) }
 }
 for _, text := range []string{
  `{"op":"define","path":"/color","value":11189196,"binding":{"family":"node","id":1,"field":"color"}}`,
  `{"op":"remove-value","path":"/color"}`,
 } { if _, err = s.CommandRaw([]byte(text)); err != nil { t.Fatal(err) } }
 if _, err = oracle.CommandRaw([]byte(`{"op":"node","id":1,"color":11189196}`)); err != nil { t.Fatal(err) }
 actual, err := s.Snapshot(); if err != nil { t.Fatal(err) }
 expected, err := oracle.Snapshot(); if err != nil || !bytes.Equal(actual, expected) { t.Fatal("packed color differs from public authoring", err) }
}

func TestGeneralAPIBatchOwnedTypedPayload(t *testing.T) {
 s, err := New(42); if err != nil { t.Fatal(err) }; defer s.Close()
 for _, command := range []string{
  `{"op":"define","path":"/task","type":"json","value":{}}`,
  `{"op":"define","path":"/name","value":""}`,
  `{"op":"define","path":"/ready","value":false}`,
  `{"op":"emit-intent","event":"/host/task","payload":{"task":{"id":"noc-1","ready":true,"items":[1,null,false]}}}`,
  `{"op":"set","path":"/task","intentId":1,"expression":{"intentPath":"/task"}}`,
  `{"op":"set","path":"/name","intentId":1,"expression":{"intentPath":"/task/id"}}`,
  `{"op":"set","path":"/ready","intentId":1,"expression":{"intentPath":"/task/ready"}}`,
  `{"op":"ack-intent","id":1}`,
 } { if _, err = s.CommandRaw([]byte(command)); err != nil { t.Fatal(err) } }
 raw, err := s.Info(); if err != nil { t.Fatal(err) }
 var info struct { Values map[string]any `json:"values"`; Intents []any `json:"intents"` }
 if err = json.Unmarshal(raw,&info); err != nil { t.Fatal(err) }
 task,ok := info.Values["/task"].(map[string]any)
 if !ok || task["id"] != "noc-1" || info.Values["/name"] != "noc-1" || info.Values["/ready"] != true || len(info.Intents) != 0 { t.Fatal("owned typed payload differs") }
 before,err := s.Snapshot();if err != nil {t.Fatal(err)}
 if _,err = s.CommandRaw([]byte(`{"op":"set","path":"/ready","value":1}`));err == nil {t.Fatal("coerced number to Boolean")}
 after,err := s.Snapshot();if err != nil || !bytes.Equal(before,after) {t.Fatal("type fault mutated state",err)}
 if _,err=s.Render();err != nil {t.Fatal(err)}
 after,err=s.Snapshot();if err != nil || !bytes.Equal(before,after) {t.Fatal("render mutated owned typed payload",err)}
 if err=s.Restore(before);err != nil {t.Fatal(err)}
}

func TestGeneralAPIBatchRetainedTypedGuardAndAction(t *testing.T) {
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 for _,command:=range []string{
  `{"op":"define","path":"/title","value":""}`,
  `{"op":"define","path":"/ready","value":true}`,
  `{"op":"trigger","id":1,"target":"/title","event":"/host/task","debounceMs":500,"whenExpression":{"and":[{"path":"/ready"},{"equal":[{"intentPath":"/task/status"},"ready"]}]},"expression":{"concat":["Task: ",{"intentPath":"/task/title"}]}}`,
  `{"op":"emit-intent","event":"/host/task","payload":{"task":{"status":"ready","title":"NOC 日本"}}}`,
 }{if _,err=s.CommandRaw([]byte(command));err!=nil{t.Fatal(err)}}
 start,err:=s.Snapshot();if err!=nil{t.Fatal(err)}
 if _,err=s.CommandRaw([]byte(`{"op":"remove-value","path":"/ready"}`));err==nil{t.Fatal("removed typed guard source")}
 unchanged,err:=s.Snapshot();if err!=nil||!bytes.Equal(start,unchanged){t.Fatal("rejection mutated state",err)}
 if err=s.AdvanceTo(500000);err!=nil{t.Fatal(err)}
 raw,err:=s.Info();if err!=nil{t.Fatal(err)}
 var info struct {Values map[string]any `json:"values"`;Intents []any `json:"intents"`}
 if err=json.Unmarshal(raw,&info);err!=nil{t.Fatal(err)}
 if info.Values["/title"]!="Task: NOC 日本"||len(info.Intents)!=1{t.Fatal("typed action/event ownership differs")}
 finish,err:=s.Snapshot();if err!=nil{t.Fatal(err)}
 if _,err=s.Render();err!=nil{t.Fatal(err)}
 unchanged,err=s.Snapshot();if err!=nil||!bytes.Equal(finish,unchanged){t.Fatal("render mutated typed action",err)}
 if err=s.Restore(start);err!=nil{t.Fatal(err)};if err=s.AdvanceTo(500000);err!=nil{t.Fatal(err)}
 unchanged,err=s.Snapshot();if err!=nil||!bytes.Equal(finish,unchanged){t.Fatal("typed action replay differs",err)}
}

func TestGeneralAPIBatchComputedJSONPreservesBinary64(t *testing.T) {
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 for _,command:=range []string{
  `{"op":"define","path":"/json","type":"json","value":0}`,
  `{"op":"set","path":"/json","expression":{"divide":[1,3]}}`,
 }{if _,err=s.CommandRaw([]byte(command));err!=nil{t.Fatal(err)}}
 snapshot,err:=s.Snapshot();if err!=nil{t.Fatal(err)}
 const offset=24+5958112+8+8+4096+24
 expected:=float64(1)/float64(3)
 if binary.LittleEndian.Uint64(snapshot[offset:offset+8])!=math.Float64bits(expected){t.Fatal("computed JSON cache loses precision")}
 raw,err:=s.Info();if err!=nil{t.Fatal(err)}
 var info struct {Values map[string]float64 `json:"values"`}
 if err=json.Unmarshal(raw,&info);err!=nil{t.Fatal(err)}
 if math.Float64bits(info.Values["/json"])!=math.Float64bits(expected){t.Fatal("JSON metadata loses precision")}
 if err=s.Restore(snapshot);err!=nil{t.Fatal(err)}
 after,err:=s.Snapshot();if err!=nil||!bytes.Equal(snapshot,after){t.Fatal("numeric JSON replay differs",err)}
}

func TestGeneralAPIBatchValueDescriptors(t *testing.T) {
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 command:=func(text string){t.Helper();if _,err:=s.CommandRaw([]byte(text));err!=nil{t.Fatal(err)}}
 for _,text:=range []string{
  `{"op":"widget","id":1,"kind":"button","text":"old"}`,
  `{"op":"define","path":"/ready","value":true,"readonly":true}`,
  `{"op":"define","path":"/title","value":"NOC","binding":{"family":"widget","id":1,"field":"text"}}`,
  `{"op":"define","path":"/task","type":"json","value":null}`,
 }{command(text)}
 start,err:=s.Snapshot();if err!=nil{t.Fatal(err)}
 type binding struct {Family string `json:"family"`;ID int `json:"id"`;Field string `json:"field"`}
 type descriptor struct {Type string `json:"type"`;Readonly bool `json:"readonly"`;Binding *binding `json:"binding"`}
 read:=func()map[string]descriptor{
  t.Helper();raw,err:=s.Info();if err!=nil{t.Fatal(err)}
  var info struct {Descriptors map[string]descriptor `json:"valueDescriptors"`}
  if err=json.Unmarshal(raw,&info);err!=nil{t.Fatal(err)};return info.Descriptors
 }
 descriptors:=read()
 if descriptors["/ready"].Type!="boolean"||!descriptors["/ready"].Readonly||descriptors["/task"].Type!="json"{t.Fatal("type/readonly contract")}
 title:=descriptors["/title"]
 if title.Type!="string"||title.Binding==nil||*title.Binding!=(binding{"widget",1,"text"}){t.Fatal("binding ownership contract")}
 pure,err:=s.Snapshot();if err!=nil||!bytes.Equal(start,pure){t.Fatal("metadata mutated state",err)}
 command(`{"op":"bind","path":"/title","binding":null}`)
 if read()["/title"].Binding!=nil{t.Fatal("detached descriptor retained binding")}
 command(`{"op":"remove-value","path":"/title"}`)
 if _,exists:=read()["/title"];exists{t.Fatal("removed descriptor remains")}
 if err=s.Restore(start);err!=nil{t.Fatal(err)}
 if read()["/title"].Binding==nil{t.Fatal("restore lost ownership")}
 restored,err:=s.Snapshot();if err!=nil||!bytes.Equal(start,restored){t.Fatal("descriptor restore changed snapshot",err)}
}

func TestGeneralAPIBatchSurfaceAndWaveBindings(t *testing.T) {
 for _,test:=range []struct {define,edit string}{
  {`{"op":"define","path":"/control","value":11259375,"binding":{"family":"surface","id":1,"field":"heatColor"}}`,`{"op":"surface","id":1,"heatColor":11259375}`},
  {`{"op":"define","path":"/control","value":false,"binding":{"family":"surface","id":1,"field":"renderVisible"}}`,`{"op":"surface","id":1,"renderVisible":false}`},
  {`{"op":"define","path":"/control","value":0.75,"binding":{"family":"surface-wave","id":1,"field":"waves.0.amplitude"}}`,`{"op":"surface-waves","surfaceId":1,"waves":[[0.75,0.2,0.3,2,0.4]]}`},
 }{
  s,err:=New(42);if err!=nil{t.Fatal(err)}
  oracle,err:=New(42);if err!=nil{s.Close();t.Fatal(err)}
  func(){defer s.Close();defer oracle.Close()
   for _,scene:=range []*Scene{s,oracle}{
    for _,command:=range []string{`{"op":"surface","id":1}`,`{"op":"surface-waves","surfaceId":1,"waves":[[1,0.2,0.3,2,0.4]]}`}{if _,err=scene.CommandRaw([]byte(command));err!=nil{t.Fatal(err)}}
   }
   if _,err=s.CommandRaw([]byte(test.define));err!=nil{t.Fatal(err)}
   if _,err=s.CommandRaw([]byte(`{"op":"remove-value","path":"/control"}`));err!=nil{t.Fatal(err)}
   if _,err=oracle.CommandRaw([]byte(test.edit));err!=nil{t.Fatal(err)}
   actual,err:=s.Snapshot();if err!=nil{t.Fatal(err)}
   expected,err:=oracle.Snapshot();if err!=nil||!bytes.Equal(actual,expected){t.Fatal("surface/wave public edit differs",err)}
  }()
 }
}

func TestGeneralAPIBatchOrderedPayloadGuard(t *testing.T) {
 s,err:=New(42);if err!=nil{t.Fatal(err)};defer s.Close()
 for _,command:=range []string{
  `{"op":"define","path":"/out","value":0}`,
  `{"op":"trigger","id":1,"target":"/out","event":"/host/metric","whenExpression":{"greaterOrEqual":[{"intentPath":"/metric"},3]},"value":7}`,
  `{"op":"emit-intent","event":"/host/metric","payload":{"metric":4}}`,
 }{if _,err=s.CommandRaw([]byte(command));err!=nil{t.Fatal(err)}}
 raw,err:=s.Info();if err!=nil{t.Fatal(err)}
 var info struct {Values map[string]float64 `json:"values"`;Intents []any `json:"intents"`}
 if err=json.Unmarshal(raw,&info);err!=nil{t.Fatal(err)}
 if info.Values["/out"]!=7||len(info.Intents)!=1{t.Fatal("ordered payload guard or event ownership differs")}
}
