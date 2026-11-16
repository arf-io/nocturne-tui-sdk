import test from 'node:test';
import assert from 'node:assert/strict';
import {accessSync, constants, copyFileSync, readFileSync, realpathSync, mkdtempSync, mkdirSync, writeFileSync, rmSync, symlinkSync, existsSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {delimiter, join, resolve, sep, dirname} from 'node:path';
import {execFileSync,spawnSync} from 'node:child_process';
import {NativeScene} from './native_scene.mjs';
import {createProject,placeComponent,prepareProject} from './composition_project.mjs';
import {generateProjectFiles} from './composition_codegen.mjs';
const native=resolve(new URL('../..',import.meta.url).pathname),wasm=readFileSync(join(native,'dist/nocturne_native.wasm'));
function rustBuildEnvironment(){
 // A build wrapper (NOCTURNE_CARGO_WRAPPER) that holds a target lock invokes Cargo by name. Select the
 // compiler's real Cargo ahead of any qualification adapter that stands in for it on PATH.
 const sysroot=execFileSync(process.env.RUSTC||'rustc',['--print','sysroot'],{encoding:'utf8',timeout:10000}).trim();
 assert(sysroot,'rustc must identify its toolchain');
 const bin=join(sysroot,'bin');accessSync(join(bin,'cargo'),constants.X_OK);
 const env={...process.env,PATH:[bin,process.env.PATH].filter(Boolean).join(delimiter),CARGO_NET_OFFLINE:'true',NOCTURNE_BUILD_SLOTS:process.env.NOCTURNE_BUILD_SLOTS||'2'};
 if(env.NOCTURNE_COVERAGE==='1'){
  // The dependency's link-arg is not propagated to this generated executable.
  // Qualification must load the same measured core used by Python and Go.
  const flags=env.CARGO_ENCODED_RUSTFLAGS!==undefined?env.CARGO_ENCODED_RUSTFLAGS.split('\x1f').filter(Boolean):(env.RUSTFLAGS||'').trim().split(/\s+/).filter(Boolean);
  env.CARGO_ENCODED_RUSTFLAGS=[...flags,'-C',`link-arg=-Wl,-rpath,${join(native,'dist')}`].join('\x1f');
 }
 return env;
}
// The command that builds a generated Rust program: the caller's wrapper (NOCTURNE_CARGO_WRAPPER), else Cargo itself.
const cargoWrapper=()=>process.env.NOCTURNE_CARGO_WRAPPER||'cargo';
function attachModel(p){const bytes=new Uint8Array(40),d=new DataView(bytes.buffer);[-20,-10,0,20,-10,0,0,20,0].forEach((n,i)=>d.setInt32(i*4,n*256,true));d.setUint32(36,0xdfa070,true);p.resources.modelRecords=Buffer.from(bytes).toString('base64');p.commands.push({op:'model-view',width:p.width,height:p.height,controls:{cameraX:0,cameraY:0,cameraZ:-85,yaw:0,pitch:0,roll:0,fov:62,projection:0,span:100,sampling:1}});}


// The compiler comes from the caller (TYPESCRIPT_COMPILER), from the bound TypeScript module
// (NOCTURNE_TYPESCRIPT_MODULE, as the qualifier sets it), or from the tsc on PATH; a fresh
// extraction has no checkout-relative toolchain layout to fall back to (fresh-sdk-07).
function resolveTypeScriptCompiler(){
  if(process.env.TYPESCRIPT_COMPILER)return process.env.TYPESCRIPT_COMPILER;
  if(process.env.NOCTURNE_TYPESCRIPT_MODULE)return resolve(process.env.NOCTURNE_TYPESCRIPT_MODULE,'../tsc.js');
  for(const dir of (process.env.PATH||'').split(delimiter)){
    const bin=join(dir,'tsc');
    if(dir&&existsSync(bin)){const candidate=resolve(dirname(realpathSync(bin)),'../lib/tsc.js');if(existsSync(candidate))return candidate;}
  }
  throw new Error('BLOCKED: tsc not available: set TYPESCRIPT_COMPILER or NOCTURNE_TYPESCRIPT_MODULE, or put tsc on PATH');
}

test('generated Node/WASM, Python and Go programs paint the same project and execute its activation',async()=>{
 const root=mkdtempSync(join(tmpdir(),'nocturne-export-')),dir=join(root,'panel');mkdirSync(dir);symlinkSync(native,join(root,'native'),'dir');const p=createProject({width:96,height:32,seed:497});p.prompt.text='文 é 👩🏽‍🚀 ` ${notCode}';p.elements=[placeComponent('button',4,8,5),placeComponent('donut',9,40,4)];p.elements[0].events.activate=[{op:'draft',text:'Activated 文 `"#',emitWeather:false}];
 p.timeline=[{timeUs:1000000,command:{op:'node',id:77,label:'Queued',position:[0,0,0]}},{timeUs:1100000,command:{op:'node',id:77,label:'Arrived'}}];attachModel(p);const files=generateProjectFiles(p);for(const [name,bytes]of Object.entries(files)){mkdirSync(resolve(dir,name,'..'),{recursive:true});writeFileSync(join(dir,name),bytes);}const scene=await NativeScene.create(wasm);prepareProject(scene,p);const initial=scene.render().bytes.slice();scene.command({op:'batch',commands:p.elements[0].events.activate});const activated=scene.render().bytes.slice();prepareProject(scene,{...p,timeUs:1200000});const later=scene.render().bytes.slice();scene.close();
 try{for(const [language,exe,args]of [['wasm',process.execPath,['panel-node.mjs']],['python',process.env.PYTHON||'python3',['panel.py']],['go',process.env.GO||'go',['run','.']]]){for(const action of ['', '4','--time=1200000']){execFileSync(exe,[...args,...(action?[action]:[])],{cwd:dir,env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'},timeout:120000,stdio:'pipe'});assert.deepEqual(new Uint8Array(readFileSync(join(dir,'panel.cells'))),action.startsWith('--time=')?later:action?activated:initial,language+' '+action);const info=JSON.parse(readFileSync(join(dir,'panel.info.json'),'utf8'));assert.equal(info.prompt.text,action==='4'?'Activated 文 `"#':p.prompt.text);}}}finally{rmSync(root,{recursive:true,force:true});}
});
test('export refuses unsupported targets and never interpolates source text as program syntax',()=>{const p=createProject();p.prompt.text='"#;panic!("bad");/* ` ${alert(1)}';const files=generateProjectFiles(p);assert(files['src/main.rs'].includes('fn main'));assert(files['panel.ts'].includes('createPanel'));assert.equal(JSON.parse(files['project.json']).prompt.text,p.prompt.text);assert(!Object.keys(files).some(p=>p.startsWith('/')||p.includes('..')));});
test('code archive preserves executable paths and every exact file byte',async()=>{const {projectCodeArchive}=await import('./composition_codegen.mjs');const p=createProject();p.prompt.text='文 🪶';const files=generateProjectFiles(p),dir=mkdtempSync(join(tmpdir(),'nocturne-zip-'));try{writeFileSync(join(dir,'panel.zip'),projectCodeArchive(p));const report=JSON.parse(execFileSync(process.env.PYTHON||'python3',['-c','import zipfile,json,hashlib,sys;z=zipfile.ZipFile(sys.argv[1]);assert z.testzip() is None;print(json.dumps({n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}))',join(dir,'panel.zip')],{encoding:'utf8'}));const {createHash}=await import('node:crypto');assert.deepEqual(report,Object.fromEntries(Object.entries(files).map(([n,v])=>[n,createHash('sha256').update(v).digest('hex')])));}finally{rmSync(dir,{recursive:true,force:true});}});
test('generated Rust and TypeScript execute the same timed project and interaction',async()=>{
 // Canonical root: tsc measures --rootDir against its real working directory.
 const root=realpathSync(mkdtempSync(join(tmpdir(),'nocturne-export-typed-'))),dir=join(root,'panel');mkdirSync(dir);symlinkSync(native,join(root,'native'),'dir');const p=createProject({width:96,height:32,seed:497});p.timeUs=700000;p.prompt.text='文 é 👩🏽‍🚀';p.elements=[placeComponent('button',4,8,5),placeComponent('field',9,40,4)];p.elements[0].events.activate=[{op:'draft',text:'Activated 文',emitWeather:false}];
 attachModel(p);for(const [name,bytes]of Object.entries(generateProjectFiles(p))){mkdirSync(resolve(dir,name,'..'),{recursive:true});writeFileSync(join(dir,name),bytes);}
 const scene=await NativeScene.create(wasm);prepareProject(scene,p);const initial=scene.render().bytes.slice();scene.command({op:'batch',commands:p.elements[0].events.activate});const activated=scene.render().bytes.slice();prepareProject(scene,{...p,timeUs:1200000});const later=scene.render().bytes.slice();scene.close();
 try{
  const compiler=resolveTypeScriptCompiler();
  // panel.ts imports ../native/bindings/typescript/contracts.js, so contracts.ts joins the
  // program. Without --outDir tsc wrote contracts.js through the native symlink into the
  // SDK's qualification fingerprint (Linux host receipt qualify-rc2-02). Emit into this
  // caller-owned root instead; --rootDir fixes the mirrored layout and --noEmitOnError
  // keeps a rejected program from writing anything.
  const emitted=join(root,'typescript-emit');
  const listing=execFileSync(process.execPath,[compiler,'--strict','--target','ES2022','--module','NodeNext','--moduleResolution','NodeNext','--rootDir',root,'--outDir',emitted,'--noEmitOnError','--listEmittedFiles','panel.ts'],{cwd:dir,timeout:120000,encoding:'utf8',stdio:'pipe'});
  const outputs=listing.split('\n').filter(line=>line.startsWith('TSFILE: ')).map(line=>resolve(line.slice(8).trim()));
  assert(outputs.length&&outputs.every(file=>file.startsWith(emitted+sep)),'tsc must emit only inside its caller-owned directory: '+outputs.join(', '));
  // The emitted panel resolves ../native/... from beside its project files.
  copyFileSync(join(emitted,'panel','panel.js'),join(dir,'panel.js'));
  writeFileSync(join(dir,'typed-run.mjs'),"import {readFile,writeFile} from 'node:fs/promises';import {createPanel} from './panel.js';const p=await createPanel(await readFile('../native/dist/nocturne_native.wasm'),await readFile('model.bin'));try{if(process.argv[2]?.startsWith('--time='))p.advance(Number(process.argv[2].slice(7)));else if(process.argv[2])p.activate(Number(process.argv[2]));await writeFile('panel.cells',p.render().bytes);await writeFile('panel.info.json',JSON.stringify(p.scene.infoComplete()));}finally{p.close();}");
  const output=execFileSync(cargoWrapper(),['build','--offline','--message-format=json'],{cwd:dir,timeout:240000,encoding:'utf8',env:rustBuildEnvironment(),stdio:['ignore','pipe','pipe']});
  const artifacts=output.split('\n').flatMap(line=>{try{return[JSON.parse(line)];}catch{return[];}}),binary=artifacts.find(x=>x.reason==='compiler-artifact'&&x.target?.name==='nocturne-panel'&&x.executable)?.executable;assert(binary,'Cargo must return the actual executable artifact');
  for(const [language,exe,args]of [['typescript',process.execPath,['typed-run.mjs']],['rust',binary,[]]])for(const action of ['', '4','--time=1200000']){execFileSync(exe,[...args,...(action?[action]:[])],{cwd:dir,timeout:120000,stdio:'pipe'});assert.deepEqual(new Uint8Array(readFileSync(join(dir,'panel.cells'))),action.startsWith('--time=')?later:action?activated:initial,language+' '+action);const info=JSON.parse(readFileSync(join(dir,'panel.info.json'),'utf8'));assert.equal(info.prompt.text,action==='4'?'Activated 文':p.prompt.text);}
 }finally{rmSync(root,{recursive:true,force:true});}
});

test('all ready projects export and execute through each native SDK language',async()=>{
 const {PROJECT_PRESETS}=await import('./composition_presets.mjs');
 for(const preset of PROJECT_PRESETS){const root=mkdtempSync(join(tmpdir(),'nocturne-preset-export-')),dir=join(root,'panel');mkdirSync(dir);symlinkSync(native,join(root,'native'),'dir');const p=preset.create(),files=generateProjectFiles(p);for(const [name,bytes]of Object.entries(files)){mkdirSync(resolve(dir,name,'..'),{recursive:true});writeFileSync(join(dir,name),bytes);}const scene=await NativeScene.create(wasm);const expected=prepareProject(scene,p).frame.bytes.slice();scene.close();
 try{const output=execFileSync(cargoWrapper(),['build','--offline','--message-format=json'],{cwd:dir,timeout:240000,encoding:'utf8',env:rustBuildEnvironment(),stdio:['ignore','pipe','pipe']});const binary=output.split('\n').flatMap(line=>{try{return[JSON.parse(line)]}catch{return[]}}).find(x=>x.reason==='compiler-artifact'&&x.target?.name==='nocturne-panel'&&x.executable)?.executable;assert(binary);
 for(const [name,exe,args]of [['wasm',process.execPath,['panel-node.mjs']],['python',process.env.PYTHON||'python3',['panel.py']],['go',process.env.GO||'go',['run','.']],['rust',binary,[]]]){execFileSync(exe,args,{cwd:dir,env:{...process.env,PYTHONDONTWRITEBYTECODE:'1'},timeout:120000,stdio:'pipe'});assert.deepEqual(new Uint8Array(readFileSync(join(dir,'panel.cells'))),expected,preset.id+' '+name);}
 }finally{rmSync(root,{recursive:true,force:true});}}
});
