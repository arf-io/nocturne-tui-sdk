/** Fleet domain state. No DOM, terminal, network, hidden clocks, or renderer access. */
export interface AgentSpec {id:string;name:string;role:string;description?:string}
export interface FleetMetrics {tokenRate:number;latencyMs:number;contextPermille:number;queue:number;tools:number;progressPermille:number}
export interface TextChunk {text:string;bornMs:number}
export interface FleetMessage {id:string;key:number;role:string;severity:string;text:string;chunks:TextChunk[];atMs:number;complete:boolean;local:boolean}
export interface AgentState extends AgentSpec {status:string;lastSeq:number;lastAtMs:number;metrics:FleetMetrics|null;history:FleetMetrics[];messages:FleetMessage[];droppedMessages:number;unread:number}
export interface FleetEvent {version:1;seq:number;agentId:string;type:string;atMs:number;payload:Record<string,unknown>}
export interface RecordedEvent {event:FleetEvent;motionMs:number}
export interface FleetCommand {version:1;commandId:string;type:'agent.message';agentId:string;text:string}
export const FLEET_LIMITS=Object.freeze({agents:32,messages:256,messageScalars:16384,eventLog:8192,history:96,chunkRuns:256,outbox:64});
const ROLES=['agent','operator','tool','system'];
const STATUSES=['running','waiting','idle','offline','error'];
/** Reject invalid scalar values before mutation. */
export function checkedInt(value:unknown,min:number,max:number,name:string):number {
 if(typeof value!=='number'||!Number.isSafeInteger(value)||value<min||value>max)throw new RangeError(`${name}: integer ${min}..${max} required`);return value;
}
function checkedText(value:unknown,name:string,max=16384):string {
 if(typeof value!=='string'||Array.from(value).length>max)throw new RangeError(`${name}: text up to ${max} scalars required`);return value;
}
function record(value:unknown,name:string):Record<string,unknown>{if(value===null||typeof value!=='object'||Array.isArray(value))throw new TypeError(`${name}: object required`);return value as Record<string,unknown>;}
function id(value:unknown,name:string):string {const text=checkedText(value,name,96);if(!/^[a-zA-Z0-9_.:-]+$/.test(text))throw new RangeError(`${name}: nonempty stable ASCII ID required`);return text;}
function pick(value:unknown,allowed:string[],name:string):string {if(typeof value!=='string'||!allowed.includes(value))throw new RangeError(`Invalid ${name}`);return value;}
function clone<T>(value:T):T{return JSON.parse(JSON.stringify(value)) as T;}
/** Bounded authoritative state. `ingest` validates an entire event before committing.
 * Sequence numbers are increasing PER AGENT; duplicates/older events return false.
 * Arrival motionMs is supplied by the host and is recorded for deterministic replay.
 * Text is retained unchanged; unsupported terminal glyphs are a presentation concern.
 */
export class FleetModel {
 readonly agents:AgentState[];
 readonly eventLog:RecordedEvent[]=[];
 revision=0;droppedEvents=0;demo=false;
 private nextMessageKey=1;
 constructor(specs:AgentSpec[]){
  if(!Array.isArray(specs)||specs.length<1||specs.length>FLEET_LIMITS.agents)throw new RangeError('1..32 agents required');
  const seen=new Set<string>();this.agents=specs.map(s=>{const agentId=id(s.id,'agent id');if(seen.has(agentId))throw new RangeError('duplicate agent id');seen.add(agentId);
   return {id:agentId,name:checkedText(s.name,'agent name',32),role:checkedText(s.role,'agent role',64),description:checkedText(s.description??'','description',256),status:'idle',lastSeq:0,lastAtMs:0,metrics:null,history:[],messages:[],droppedMessages:0,unread:0};});
 }
 /** Find an existing agent; throws for unknown IDs. Never auto-creates identities. */
 agent(agentId:string):AgentState {const a=this.agents.find(a=>a.id===agentId);if(!a)throw new RangeError(`Unknown agent ${agentId}`);return a;}
 private appendMessage(a:AgentState,message:FleetMessage):void {a.messages.push(message);if(a.messages.length>FLEET_LIMITS.messages){a.messages.shift();a.droppedMessages++;}}
 /** Validate/commit one version-1 Fleet event. Returns false for stale sequence numbers.
  * Throws TypeError/RangeError for malformed, unknown-agent/message or oversized data.
  * Example: model.ingest({version:1,seq:1,agentId:'atlas',type:'status',atMs:0,payload:{status:'running'}},0).
  */
 ingest(input:unknown,motionMs:number):boolean {
  checkedInt(motionMs,0,Number.MAX_SAFE_INTEGER,'motionMs');const e=record(input,'event');
  if(e.version!==1)throw new RangeError('Fleet event version must be 1');const a=this.agent(id(e.agentId,'agentId'));
  const seq=checkedInt(e.seq,1,Number.MAX_SAFE_INTEGER,'seq'),atMs=checkedInt(e.atMs,0,Number.MAX_SAFE_INTEGER,'atMs');
  const type=pick(e.type,['telemetry','status','message.start','message.delta','message.end'],'event type');const p=record(e.payload,'payload');
  // Duplicates carry no authority and cannot alter timestamps or reveal timing.
  if(seq<=a.lastSeq)return false;
  let commit:()=>void;let payload:Record<string,unknown>;
  if(type==='telemetry'){
   const m:FleetMetrics={tokenRate:checkedInt(p.tokenRate,0,1000000,'tokenRate'),latencyMs:checkedInt(p.latencyMs,0,1000000,'latencyMs'),contextPermille:checkedInt(p.contextPermille,0,1000,'contextPermille'),queue:checkedInt(p.queue,0,1000000,'queue'),tools:checkedInt(p.tools,0,1000000,'tools'),progressPermille:checkedInt(p.progressPermille,0,1000,'progressPermille')};
   payload={...m};commit=()=>{a.metrics=m;a.history.push({...m});if(a.history.length>FLEET_LIMITS.history)a.history.shift();};
  }else if(type==='status') {const status=pick(p.status,STATUSES,'status');payload={status};commit=()=>{a.status=status;};
  }else if(type==='message.start'){
   const messageId=id(p.messageId,'messageId');if(a.messages.some(m=>m.id===messageId))throw new RangeError('duplicate message ID');
   const text=checkedText(p.text??'','text'),role=pick(p.role,ROLES,'role'),severity=pick(p.severity??'normal',['normal','warning','error'],'severity');
   payload={messageId,role,severity,text};commit=()=>{this.appendMessage(a,{id:messageId,key:this.nextMessageKey++,role,severity,text,chunks:text?[{text,bornMs:motionMs}]:[],atMs,complete:false,local:false});a.unread++;};
  }else {
   const messageId=id(p.messageId,'messageId'),m=a.messages.find(m=>m.id===messageId);if(!m)throw new RangeError('unknown message ID');
   if(type==='message.end'){payload={messageId};commit=()=>{m.complete=true;};}
   else {if(m.complete)throw new RangeError('cannot append to a completed message');const text=checkedText(p.text,'text');if(Array.from(m.text).length+Array.from(text).length>FLEET_LIMITS.messageScalars)throw new RangeError('message capacity');
    payload={messageId,text};commit=()=>{m.text+=text;if(text)m.chunks.push({text,bornMs:motionMs});if(m.chunks.length>FLEET_LIMITS.chunkRuns){const old=m.chunks.splice(0,128);m.chunks.unshift({text:old.map(c=>c.text).join(''),bornMs:old[0].bornMs});}};
   }
  }
  // Only normalized scalar payloads enter the replay log. Unknown/cyclic extra
  // properties cannot cause a post-commit JSON serialization failure.
  const normalized:FleetEvent={version:1,seq,agentId:a.id,type,atMs,payload};
  // All validation above; domain state and replay log commit together.
  commit();a.lastSeq=seq;a.lastAtMs=atMs;this.revision++;
  this.eventLog.push({event:normalized,motionMs});if(this.eventLog.length>FLEET_LIMITS.eventLog){this.eventLog.shift();this.droppedEvents++;}return true;
 }
 /** Append a LOCAL operator message. This does not consume an upstream sequence or
  * claim network delivery; only the host's explicit command adapter can send it.
  */
 localMessage(agentId:string,messageId:string,text:string,motionMs:number):void {
  const a=this.agent(agentId);checkedText(text,'text');checkedInt(motionMs,0,Number.MAX_SAFE_INTEGER,'motionMs');
  this.appendMessage(a,{id:messageId,key:this.nextMessageKey++,role:'operator',severity:'normal',text,chunks:[{text,bornMs:motionMs}],atMs:a.lastAtMs,complete:true,local:true});this.revision++;
 }
 /** JSON-safe diagnostic snapshot. No credentials or runtime functions are included. */
 snapshot():object{return {version:1,demo:this.demo,revision:this.revision,droppedEvents:this.droppedEvents,agents:clone(this.agents)};}
 /** Lossless retained text. Display fading never changes exported transcript data. */
 transcript(agentId:string):string {return this.agent(agentId).messages.map(m=>`${m.role.toUpperCase()}${m.local?' [local/outbound]':''}${m.severity!=='normal'?' ['+m.severity+']':''}\n${m.text}`).join('\n\n');}
}
export interface TranscriptRun {text:string;bornMs:number}
export interface TranscriptLine {messageKey:number;messageId:string;role:string;severity:string;label:boolean;runs:TranscriptRun[];lineIndex:number}
/** Stateless wrapping/viewport helper. All lengths are Unicode scalars, matching
 * the renderer's documented narrow glyph profile, not full grapheme layout.
 */
export class TranscriptViewport {
 /** Wrap text without losing content or resetting arrival timestamps. Blank
  * separators and role labels are explicit rows. Width <=0 returns an empty list.
  */
 static wrap(messages:FleetMessage[],width:number):TranscriptLine[]{
  if(width<=0)return [];checkedInt(width,1,512,'transcript width');const lines:TranscriptLine[]=[];
  for(const m of messages){let index=0;const base={messageKey:m.key,messageId:m.id,role:m.role,severity:m.severity};
   lines.push({...base,label:true,runs:[{text:`${m.role.toUpperCase()}${m.local?' / LOCAL OUTBOUND':''}${m.severity!=='normal'?' / '+m.severity.toUpperCase():''}`,bornMs:m.chunks[0]?.bornMs??0}],lineIndex:index++});
   // Word boundaries are presentation breaks; preserve each scalar's birth time.
   const chars:{glyph:string;bornMs:number}[]=[];
   for(const chunk of m.chunks)for(const glyph of Array.from(chunk.text))if(glyph!=='\r')chars.push({glyph:glyph==='\t'?' ':glyph,bornMs:chunk.bornMs});
   let cursor=0;
   while(cursor<chars.length){
    let end=Math.min(chars.length,cursor+width),newline=-1;
    for(let i=cursor;i<end;i++)if(chars[i].glyph==='\n'){newline=i;break;}
    if(newline>=0)end=newline;
    else if(end<chars.length&&chars[end].glyph!==' '&&chars[end].glyph!=='\n'){
     for(let i=end-1;i>cursor;i--)if(chars[i].glyph===' '){end=i+1;break;}
    }
    const runs:TranscriptRun[]=[];
    for(let i=cursor;i<end;i++){const ch=chars[i],last=runs[runs.length-1];if(last&&last.bornMs===ch.bornMs)last.text+=ch.glyph;else runs.push({text:ch.glyph,bornMs:ch.bornMs});}
    lines.push({...base,label:false,runs,lineIndex:index++});cursor=end;
    if(cursor<chars.length&&chars[cursor].glyph==='\n')cursor++;
   }
   if(!chars.length)lines.push({...base,label:false,runs:[],lineIndex:index++});
   lines.push({...base,label:false,runs:[],lineIndex:index});
  }return lines;
 }
 /** Return the bottom-anchored window, or a history window offset in whole rows. */
 static visible(lines:TranscriptLine[],height:number,offset:number):TranscriptLine[]{if(height<=0)return [];const end=Math.max(0,lines.length-Math.max(0,offset));return lines.slice(Math.max(0,end-height),end);}
}
export const DEMO_AGENTS:AgentSpec[]=[
 {id:'atlas',name:'ATLAS',role:'Coordinator',description:'Task graph, routing, synthesis'},
 {id:'prism',name:'PRISM',role:'Research',description:'Sources, alternatives, evidence'},
 {id:'forge',name:'FORGE',role:'Implementation',description:'Worktree, patches, tests'},
 {id:'quill',name:'QUILL',role:'Review',description:'Correctness, docs, edge cases'},
 {id:'sentinel',name:'SENTINEL',role:'Policy',description:'Approval gates, bounded actions'},
 {id:'relay',name:'RELAY',role:'Routing',description:'Provider health, queue pressure'},
 {id:'scribe',name:'SCRIBE',role:'Archive',description:'Provenance, artifacts, indexing'},
 {id:'echo',name:'ECHO',role:'Communication',description:'Agent party line, operator notes'}
];
export const DEMO_NOTES=[
 'The route map is stable. I am comparing two capacity profiles before moving the build queue.',
 'Research and implementation share the same task. PRISM owns the evidence; FORGE owns the patch. Both feed the review node.',
 'A newer telemetry sample is available. The values below are committed immediately, even while the decorative clock is held.',
 'The context envelope is approaching its soft limit. I have marked a handoff point without discarding the current transcript.',
 'I found one dependency worth isolating. The review can proceed independently while the slower source check completes.',
 'The scope shows measured samples, not a made-up activity animation. In this offline study, those samples come from a labeled synthetic source.',
 'The checkpoint contains the task identity, remaining work, and the current evidence list. No command has been executed by this preview.',
 'I will keep collecting updates while you read earlier messages. Live-tail following resumes only when you request it.',
 'The visual contract is simple: data now, light in motion. Neither a transition nor a fade delays the underlying event.',
 'Review complete for this simulated work unit. The next step remains visible in the activity stream.'
];
/** Deterministic example telemetry, not a measurement of a real system. */
export function demoMetrics(agentIndex:number,tick:number):FleetMetrics {
 const wave=(phase:number)=>.7*Math.sin(tick*.10)+.55*Math.sin(tick*.14+phase)+.35*Math.sin(tick*.27+phase*.7);
 return {tokenRate:Math.max(0,Math.round(45+agentIndex*5+wave(agentIndex)*32)),latencyMs:Math.round(180+agentIndex*17+wave(agentIndex+2)*65),contextPermille:Math.round(360+agentIndex*48+wave(agentIndex+5)*100),queue:Math.max(0,Math.round(2+wave(agentIndex+8)*2)),tools:12+agentIndex*3+Math.floor(tick/30),progressPermille:Math.min(980,420+agentIndex*43+Math.floor(tick/8)%100)};
}
/** Create a clearly labeled offline fixture fleet, with a seeded sample history.
 * This factory never contacts endpoints or claims to represent the user's agents.
 */
export function createDemoFleet():FleetModel {
 const m=new FleetModel(DEMO_AGENTS);m.demo=true;
 m.agents.forEach((a,i)=>{
  for(let t=0;t<96;t++)m.ingest({version:1,agentId:a.id,seq:a.lastSeq+1,type:'telemetry',atMs:t*100,payload:{...demoMetrics(i,t)}},0);
  m.ingest({version:1,agentId:a.id,seq:a.lastSeq+1,type:'status',atMs:9600,payload:{status:i===4?'waiting':i===6?'idle':'running'}},0);
  for(let j=0;j<9;j++)m.ingest({version:1,agentId:a.id,seq:a.lastSeq+1,type:'message.start',atMs:9600+j*20,payload:{messageId:`seed-${j}`,role:j%4===0?'operator':j%4===2?'tool':'agent',text:DEMO_NOTES[(j+i)%DEMO_NOTES.length],severity:'normal'}},0);
  a.unread=0;
 });return m;
}
