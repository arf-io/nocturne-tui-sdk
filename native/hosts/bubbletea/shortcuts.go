package main
import("fmt";"strings";native "nocturne/native")
type shortcutProfile struct{bindings map[string]uint32;managed map[string]bool;hints string}
type shortcutAction struct{id uint32;label string;preferences []string}
var shortcutActions=[]shortcutAction{{1,"Quit",[]string{"ctrl+q","alt+q"}},{2,"Hold",[]string{"ctrl+p","alt+p"}},{3,"Copy",[]string{"alt+w","alt+c"}},{4,"Cut",[]string{"ctrl+w","alt+x"}},{5,"Paste",[]string{"ctrl+y","alt+v"}},{6,"Help",[]string{"f1","f7"}},{7,"Reader",[]string{"f6","f8"}}}
func shortcutChord(name string)(uint32,uint32,error){
 if strings.HasPrefix(name,"f"){var n int;if _,e:=fmt.Sscanf(name,"f%d",&n);e==nil&&n>=1&&n<=12&&name==fmt.Sprintf("f%d",n){return 0x110000+uint32(n),0,nil}}
 for prefix,mod:=range map[string]uint32{"ctrl+":2,"alt+":4}{if strings.HasPrefix(name,prefix){key:=strings.TrimPrefix(name,prefix);if len(key)==1&&key[0]>='a'&&key[0]<='z'{return uint32(key[0]),mod,nil}}}
 return 0,0,fmt.Errorf("unknown normalized shortcut %q",name)
}
func negotiateShortcuts(reserved []string)(*shortcutProfile,error){
 p:=&shortcutProfile{bindings:map[string]uint32{},managed:map[string]bool{}};var actions []uint32;var candidates,host [][3]uint32;var names []string
 for _,action:=range shortcutActions{actions=append(actions,action.id);for _,name:=range action.preferences{k,m,e:=shortcutChord(name);if e!=nil{return nil,e};candidates=append(candidates,[3]uint32{action.id,k,m});if !p.managed[name]{p.managed[name]=true;names=append(names,name);host=append(host,[3]uint32{k,m,0})}}}
 for _,name:=range reserved{if !p.managed[name]{return nil,fmt.Errorf("reservation outside managed shortcuts: %s",name)};for i,n:=range names{if n==name{host[i][2]=1}}}
 rows,e:=native.NegotiateShortcuts(actions,candidates,host);if e!=nil{return nil,e};var hints []string
 for i,row:=range rows{name:="unassigned";if row[3]!=0{for j,h:=range host{if h[0]==row[1]&&h[1]==row[2]{name=names[j];p.bindings[name]=row[0];break}}};hints=append(hints,shortcutActions[i].label+": "+name)}
 p.hints=strings.Join(hints," | ");return p,nil
}
func(m *model)ensureShortcuts(){if m.shortcuts==nil&&m.err==nil{m.shortcuts,m.err=negotiateShortcuts(m.reservedShortcuts)}}
