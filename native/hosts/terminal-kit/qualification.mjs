/** Test-only launcher: real terminal, real Terminal Kit, real current NativeScene.
 * Failure hooks are local JavaScript functions, not native/public runtime commands.
 */
import fs from 'node:fs';
import {NativeScene} from '../../bindings/typescript/native_scene.mjs';
import {startHost} from './host.mjs';
const scenario=process.env.NOCTURNE_TEST_SCENARIO;
if(!['normal','input','pointer','ctrlc','paste-reject','error','exception','rejection','setup',
 'modal','wheel','focus','prompt-marquee','prompt-grow','prompt-vim-inline','prompt-vim-full','graph','unicode','latency','backpressure'].includes(scenario))throw Error('Explicit qualification scenario required');
const trace=fs.openSync(process.env.NOCTURNE_TEST_TRACE,'wx',0o600);let bytes=0;
const scene=await NativeScene.create(fs.readFileSync(new URL('../../dist/nocturne_native.wasm',import.meta.url)));
const record=(event,s,f)=>{
 const frame=s.render(),view=new DataView(frame.bytes.buffer,frame.bytes.byteOffset,frame.bytes.byteLength),nodeHits={};
 for(let i=0;i<frame.width*frame.height;i++){
  const owner=view.getUint32(i*16+12,true);
  if((owner&0xff000000)===0x10000000)nodeHits[owner&0xffff]??=[i%frame.width,Math.floor(i/frame.width)];
 }
 const line=JSON.stringify({event,info:s.info(),...f,nodeHits})+'\n';bytes+=Buffer.byteLength(line);if(bytes>16*1024*1024)throw Error('trace bound');fs.writeSync(trace,line);
};
try{
 for(const line of fs.readFileSync(process.env.NOCTURNE_TEST_FIXTURE,'utf8').trim().split('\n'))scene.command(JSON.parse(line));
 await startHost({scene,paused:!['normal','backpressure'].includes(scenario),observe:record,
  beforeEvent(kind,name,s){
   if(kind==='key'&&name==='CTRL_T'){
    if(scenario==='error')s.command({op:'invalid-qualification-command'});
    if(scenario==='exception')setImmediate(()=>{throw Error('intentional qualification exception')});
    if(scenario==='rejection')setImmediate(()=>{Promise.reject(Error('intentional qualification rejection'))});
   }
  },
  async afterEnter(term,s){
   if(scenario==='setup'){
    record('setup-raw',s);
    await new Promise((resolve,reject)=>{term.once('key',name=>{if(name==='CTRL_Q')reject(Error('intentional partial-startup failure'));else reject(Error('wrong setup handshake'))})});
   }
  }
 });
}catch(e){console.error(e);process.exitCode=1}
finally{scene.close();fs.closeSync(trace)}
