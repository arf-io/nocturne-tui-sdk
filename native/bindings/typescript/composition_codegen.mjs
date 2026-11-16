import {projectPlan,exportProject,decodeProjectModel} from './composition_project.mjs';
const literal=value=>JSON.stringify(value).replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');
function rustString(text){let hashes='#';while(text.includes('"'+hashes))hashes+='#';return 'r'+hashes+'"'+text+'"'+hashes;}
export function generateProjectFiles(value){
 const plan=projectPlan(value),commands=plan.commands.slice(1),reset=plan.commands[0],actions=Object.fromEntries(plan.interactions.map(x=>[x.id,{op:'batch',commands:x.commands}])),model=plan.modelRecords!==null;
 const js=`import {NativeScene} from '../native/bindings/typescript/native_scene.mjs';
const reset=${literal(reset)},commands=${literal(commands)},actions=${literal(actions)},owners=${literal(plan.interactions.map(x=>[x.owner,x.id]))},timeline=${literal(plan.timeline)};
export async function createPanel(wasm,modelBytes){
 const scene=await NativeScene.create(wasm,${plan.seed});let next=0;
 const advance=timeUs=>{while(next<timeline.length&&timeline[next].timeUs<=timeUs){while(scene.command({op:'time',timeUs:timeline[next].timeUs})===1){}while(scene.command(timeline[next].command)===1){}next++;}while(scene.command({op:'time',timeUs})===1){}return scene.render();};
 try {scene.command(reset);${model?'if(!(modelBytes instanceof Uint8Array))throw Error("model.bin is required");scene.setModelRecords(modelBytes);':''}for(const command of commands)while(scene.command(command)===1){}}catch(error){scene.close();throw error;}
 return {scene,render:()=>scene.render(),advance,
 activate:id=>{const action=actions[id];if(!action)return false;scene.command(action);return true;},
 pointer:(phase,x,y,button=0)=>{scene.render();scene.command({op:'pointer',phase,x,y,button});if(phase==='up'&&!scene.infoComplete().modal&&!scene.infoComplete().sourceModal?.blocking){const frame=scene.render(),owner=frame.cells[(Math.floor(y)*frame.width+Math.floor(x))*4+3],hit=owners.find(([o])=>o===owner);if(hit&&actions[hit[1]])scene.command(actions[hit[1]]);}return scene.render();},
 key:key=>scene.command({op:'key',key}),input:text=>scene.command({op:'input',text}),paste:text=>scene.command({op:'paste',text}),close:()=>scene.close()};
}
`;
 const node=`import {readFile,writeFile} from 'node:fs/promises';
import {createPanel} from './panel.mjs';
const panel=await createPanel(await readFile(new URL('../native/dist/nocturne_native.wasm',import.meta.url))${model?",await readFile(new URL('./model.bin',import.meta.url))":''});
try{if(process.argv[2]?.startsWith('--time='))panel.advance(Number(process.argv[2].slice(7)));else if(process.argv[2]&&!panel.activate(Number(process.argv[2])))throw Error('Unknown activation ID');await writeFile('panel.cells',panel.render().bytes);await writeFile('panel.info.json',JSON.stringify(panel.scene.infoComplete()));}finally{panel.close();}
`;
 const py=`from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'native/bindings/python'))
from nocturne_native import NativeScene
RESET=json.loads(${literal(JSON.stringify(reset))})
COMMANDS=json.loads(${literal(JSON.stringify(commands))})
ACTIONS=json.loads(${literal(JSON.stringify(actions))})
TIMELINE=json.loads(${literal(JSON.stringify(plan.timeline))})
def advance(scene,time_us,state):
    while state[0]<len(TIMELINE) and TIMELINE[state[0]]['timeUs']<=time_us:
        event=TIMELINE[state[0]]
        while scene.command({'op':'time','timeUs':event['timeUs']})==1: pass
        while scene.command(event['command'])==1: pass
        state[0]+=1
    while scene.command({'op':'time','timeUs':time_us})==1: pass
def activate(scene,element_id):
    command=ACTIONS.get(str(element_id))
    if command is None: return False
    scene.command(command)
    return True
with NativeScene(seed=${plan.seed}) as scene:
    scene.command(RESET)
${model?"    scene.set_model_records(Path(__file__).with_name('model.bin').read_bytes())\n":''}    for command in COMMANDS:
        while scene.command(command)==1: pass
    if len(sys.argv)>1:
        if sys.argv[1].startswith('--time='): advance(scene,int(sys.argv[1][7:]),[0])
        elif not activate(scene,int(sys.argv[1])): raise ValueError('Unknown activation ID')
    Path('panel.cells').write_bytes(scene.render().bytes)
    Path('panel.info.json').write_text(json.dumps(scene.info_complete(),ensure_ascii=False))
`;
 const go=`package main
import("os";"fmt";"strconv";"strings";native "nocturne/native")
var actions=map[int]string{${Object.entries(actions).map(([id,cmd])=>`${id}:${literal(JSON.stringify(cmd))}`).join(',')}}
func Activate(scene *native.Scene,id int)(bool,error){command,ok:=actions[id];if !ok{return false,nil};_,err:=scene.CommandRaw([]byte(command));return true,err}
var timeline=[]struct{time uint64;command string}{${plan.timeline.map(e=>`{${e.timeUs},${literal(JSON.stringify(e.command))}}`).join(',')}}
func Advance(scene *native.Scene,timeUs uint64,next *int)error{for *next<len(timeline)&&timeline[*next].time<=timeUs{event:=timeline[*next];for _,command:=range []string{fmt.Sprintf(${literal('{"op":"time","timeUs":%d}')},event.time),event.command}{for{pending,e:=scene.CommandRaw([]byte(command));if e!=nil{return e};if pending!=1{break}}};*next++};for{pending,e:=scene.CommandRaw([]byte(fmt.Sprintf(${literal('{"op":"time","timeUs":%d}')},timeUs)));if e!=nil{return e};if pending!=1{return nil}}}
func run()error{scene,err:=native.New(${plan.seed});if err!=nil{return err};defer scene.Close()
 if _,err=scene.CommandRaw([]byte(${literal(JSON.stringify(reset))}));err!=nil{return err}
 ${model?'records,err:=os.ReadFile("model.bin");if err!=nil{return err};if err=scene.SetModelRecords(records);err!=nil{return err}':''}
 for _,command:=range []string{${commands.map(c=>literal(JSON.stringify(c))).join(",")}}{for{pending,e:=scene.CommandRaw([]byte(command));if e!=nil{return e};if pending!=1{break}}}
 if len(os.Args)>1&&strings.HasPrefix(os.Args[1],"--time="){target,e:=strconv.ParseUint(os.Args[1][7:],10,64);if e!=nil{return e};next:=0;if e=Advance(scene,target,&next);e!=nil{return e}}else if len(os.Args)>1{id,e:=strconv.Atoi(os.Args[1]);if e!=nil{return e};ok,e:=Activate(scene,id);if e!=nil{return e};if !ok{return fmt.Errorf("unknown activation ID")}}
 frame,err:=scene.Render();if err!=nil{return err};if err=os.WriteFile("panel.cells",frame.Bytes,0600);err!=nil{return err};info,err:=scene.InfoComplete();if err!=nil{return err};return os.WriteFile("panel.info.json",info,0600)}
func main(){if err:=run();err!=nil{fmt.Fprintln(os.Stderr,err);os.Exit(1)}}
`;
 const rs=`use nocturne_native::NativeScene;
fn activate(scene:&mut NativeScene,id:u32)->Result<bool,String>{let command=match id{${Object.entries(actions).map(([id,cmd])=>`${id}=>${rustString(JSON.stringify(cmd))}`).join(',')}${Object.keys(actions).length?',':''}_=>return Ok(false)};scene.command(command)?;Ok(true)}
fn advance(scene:&mut NativeScene,time_us:u64,next:&mut usize)->Result<(),String>{let timeline:&[(u64,&str)]=&[${plan.timeline.map(e=>`(${e.timeUs},${rustString(JSON.stringify(e.command))})`).join(',')}];while *next<timeline.len()&&timeline[*next].0<=time_us{let event=timeline[*next];while scene.command(&format!(r#"{{\"op\":\"time\",\"timeUs\":{}}}"#,event.0))?{}while scene.command(event.1)?{}*next+=1;}while scene.command(&format!(r#"{{\"op\":\"time\",\"timeUs\":{}}}"#,time_us))?{}Ok(())}
fn main()->Result<(),Box<dyn std::error::Error>>{let mut scene=NativeScene::new(${plan.seed})?;
 scene.command(${rustString(JSON.stringify(reset))})?;
 ${model?'scene.set_model_records(&std::fs::read("model.bin")?)?;':''}
 for command in [${commands.map(c=>rustString(JSON.stringify(c))).join(",")}] {while scene.command(command)? {}}
 if let Some(id)=std::env::args().nth(1){if let Some(target)=id.strip_prefix("--time="){advance(&mut scene,target.parse()?,&mut 0)?;}else if !activate(&mut scene,id.parse()?)?{return Err("Unknown activation ID".into());}}
 std::fs::write("panel.cells",scene.render()?.bytes)?;std::fs::write("panel.info.json",scene.infoComplete()?)?;Ok(())}
`;
 const ts=`import {NativeScene} from '../native/bindings/typescript/native_scene.mjs';
import type {NativeCommand} from '../native/bindings/typescript/contracts.js';
const reset:NativeCommand=${literal(reset)},commands:NativeCommand[]=${literal(commands)};
const actions:Record<number,NativeCommand>=${literal(actions)},timeline:Array<{timeUs:number;command:NativeCommand}>=${literal(plan.timeline)};
export async function createPanel(wasm:BufferSource,modelBytes?:Uint8Array){const scene=await NativeScene.create(wasm,${plan.seed});let next=0;const advance=(timeUs:number)=>{while(next<timeline.length&&timeline[next].timeUs<=timeUs){while(scene.command({op:'time',timeUs:timeline[next].timeUs})===1){}while(scene.command(timeline[next].command)===1){}next++;}while(scene.command({op:'time',timeUs})===1){}return scene.render();};try{scene.command(reset);${model?'if(!modelBytes)throw Error("model.bin is required");scene.setModelRecords(modelBytes);':''}for(const command of commands)while(scene.command(command)===1){}}catch(error){scene.close();throw error;}return {scene,advance,render:()=>scene.render(),activate:(id:number)=>{if(!actions[id])return false;scene.command(actions[id]);return true;},input:(text:string)=>scene.command({op:'input',text}),key:(key:string)=>scene.command({op:'key',key}),close:()=>scene.close()};}
`;
 const files={'project.json':exportProject(value),'package.json':'{"type":"module","private":true}\n','panel.mjs':js,'panel-node.mjs':node,'panel.ts':ts,'panel.py':py,'main.go':go,'go.mod':'module nocturne-panel\n\ngo 1.22\n\nrequire nocturne/native v0.0.0\nreplace nocturne/native => ../native/bindings/go\n','src/main.rs':rs,'Cargo.toml':'[package]\nname = "nocturne-panel"\nversion = "0.1.0"\nedition = "2021"\n\n[dependencies]\nnocturne-native = { path = "../native/bindings/rust" }\n','README.md':'# '+value.name.replace(/[\r\n]/g,' ')+'\n\nPut this directory beside the SDK `native/` directory. Build the SDK before running the native programs.\n\n- WASM: `node panel-node.mjs`\n- Python: `python3 panel.py`\n- Go: `go run .`\n- Rust: `cargo run --offline`\n\nEach program writes `panel.cells` (little-endian glyph, foreground, background, owner) and `panel.info.json`. Pass `--time=1200000` to advance through due timeline actions. The exported advance helpers retain the next action index between calls. An optional numeric argument invokes that element’s activation transaction.\n\nFor a browser host, import `createPanel` from `panel.mjs`, supply the SDK WASM bytes'+(model?' and `model.bin` bytes':'')+', display `render().cells`, and forward cell coordinates through `pointer`, `key`, `input` and `paste`. The TypeScript entry exports the same scene for typed host integration. Native hosts forward pointer/key/input commands through the returned SDK scene.\n'};
 if(model)files['model.bin']=decodeProjectModel(plan.modelRecords);return files;
}
export function projectCodeArchive(project){
 const files=generateProjectFiles(project),encoder=new TextEncoder(),local=[],central=[];let offset=0,centralSize=0;
 const crc=bytes=>{let c=0xffffffff;for(const byte of bytes){c^=byte;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return(c^0xffffffff)>>>0;};
 for(const [name,value]of Object.entries(files)){const path=encoder.encode(name),data=typeof value==='string'?encoder.encode(value):value,checksum=crc(data),head=new Uint8Array(30+path.length),a=new DataView(head.buffer),record=new Uint8Array(46+path.length),b=new DataView(record.buffer);
  if(data.length>0xffffffff||offset+head.length+data.length>0xffffffff)throw RangeError('ZIP32 file range exceeded');
  a.setUint32(0,0x04034b50,true);a.setUint16(4,20,true);a.setUint16(6,0x800,true);a.setUint16(12,33,true);a.setUint32(14,checksum,true);a.setUint32(18,data.length,true);a.setUint32(22,data.length,true);a.setUint16(26,path.length,true);head.set(path,30);
  b.setUint32(0,0x02014b50,true);b.setUint16(4,20,true);b.setUint16(6,20,true);b.setUint16(8,0x800,true);b.setUint16(14,33,true);b.setUint32(16,checksum,true);b.setUint32(20,data.length,true);b.setUint32(24,data.length,true);b.setUint16(28,path.length,true);b.setUint32(42,offset,true);record.set(path,46);local.push(head,data);central.push(record);offset+=head.length+data.length;centralSize+=record.length;
 }
 const end=new Uint8Array(22),v=new DataView(end.buffer);v.setUint32(0,0x06054b50,true);v.setUint16(8,central.length,true);v.setUint16(10,central.length,true);v.setUint32(12,centralSize,true);v.setUint32(16,offset,true);const result=new Uint8Array(offset+centralSize+22);let at=0;for(const bytes of [...local,...central,end]){result.set(bytes,at);at+=bytes.length;}return result;
}
