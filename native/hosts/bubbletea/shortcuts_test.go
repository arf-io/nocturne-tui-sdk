package main
import("bytes";"strings";"testing";tea "github.com/charmbracelet/bubbletea")
func TestNegotiatedBubbleTeaClipboardAndReservedKeys(t *testing.T){
 m:=testModel(t);m.shortcuts=nil;m.reservedShortcuts=[]string{"ctrl+q","alt+w","ctrl+w","ctrl+y","f1"};m.shortcutToolbar=true;m.ensureShortcuts();if m.err!=nil{t.Fatal(m.err)}
 if !strings.Contains(m.View(),"Quit: alt+q")||!strings.Contains(m.View(),"Help: f7"){t.Fatal(m.View())}
 m.apply(map[string]any{"op":"draft","text":"AéZ","emitWeather":false});m.apply(map[string]any{"op":"select","anchor":1,"caret":3});before,_:=m.scene.Snapshot()
 next,cmd:=m.Update(tea.KeyMsg{Type:tea.KeyCtrlQ});m=next.(model);after,_:=m.scene.Snapshot();if cmd!=nil||!bytes.Equal(before,after){t.Fatal("reserved quit changed state or exited")}
 for _,key:=range []rune{'c','x','v'}{next,_=m.Update(tea.KeyMsg{Type:tea.KeyRunes,Runes:[]rune{key},Alt:true});m=next.(model)}
 text,e:=m.scene.TextRunSource(0,0);if e!=nil||text!="AéZ"||m.clipboard!="é"{t.Fatal(text,m.clipboard,e)}
 _,cmd=m.Update(tea.KeyMsg{Type:tea.KeyRunes,Runes:[]rune{'q'},Alt:true});if cmd==nil{t.Fatal("assigned quit did not exit")}
}
func TestShortcutProfileRejectsUnknownAndReportsUnassigned(t *testing.T){
 p,e:=negotiateShortcuts([]string{"ctrl+q","alt+q"});if e!=nil||!strings.Contains(p.hints,"Quit: unassigned"){t.Fatal(p,e)}
 if _,e=negotiateShortcuts([]string{"ctrl+c"});e==nil{t.Fatal("emergency chord accepted as managed")}
}
