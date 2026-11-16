/** One scalar-indexed draft with multiple views. No filesystem, wall clock, or
 * terminal ownership. Mode changes are presentation only; no command discards
 * this document. This is a documented Vim-style subset, not embedded Vim. */
export const PROMPT_MODES = ['marquee','grow','vim-inline','vim-full'];
export const PROMPT_BORDERS = ['none','rounded','square','double','heavy'];
export const DEFAULT_PROMPT = Object.freeze({alpha:0.32,background:'#10161e',foreground:'#dedbd2',accent:'#8ccfc4',
 border:'rounded',paddingX:1,paddingY:0,margin:1,minRows:1,maxRows:7,inlineRows:12,inlineWidth:88,
 lineNumbers:true,active:true,selected:false,hueStep:0,hueSpeed:0,huePeriodMs:1000,
 maxChars:65536,selectionColor:'#385763'});
const PROMPT_LIMITS={alpha:[0,1],paddingX:[0,8],paddingY:[0,4],margin:[0,6],minRows:[1,24],maxRows:[1,60],inlineRows:[5,80],inlineWidth:[24,240],hueStep:[-360,360],hueSpeed:[-360,360],huePeriodMs:[1,120000],maxChars:[1,65536]};
const bounded=(n,a,b)=>Math.max(a,Math.min(b,n));
const arr=s=>[...s];
/** Validate a complete proposed configuration before committing it. */
export function validatePrompt(input={}) {
 const out={...DEFAULT_PROMPT,...input};
 for(const [k,v]of Object.entries(out)){
  if(!(k in DEFAULT_PROMPT))throw RangeError('Unknown prompt setting: '+k);
  if(k in PROMPT_LIMITS){const [lo,hi]=PROMPT_LIMITS[k];if(typeof v!=='number'||!Number.isFinite(v)||v<lo||v>hi||(!['alpha','hueStep','hueSpeed'].includes(k)&&!Number.isInteger(v)))throw RangeError('Invalid prompt '+k);}
  else if(['background','foreground','accent','selectionColor'].includes(k)){if(typeof v!=='string'||!/^#[0-9a-f]{6}$/i.test(v))throw RangeError('RGB hex required for '+k);}
  else if(k==='border'){if(!PROMPT_BORDERS.includes(v))throw RangeError('prompt border');}
  else if(typeof v!=='boolean')throw RangeError('Boolean prompt '+k);
 }
 if(out.minRows>out.maxRows)throw RangeError('minRows exceeds maxRows');
 return out;
}
/** Map all scalar boundaries to logical wrapped rows. Newlines are stored, not
 * flattened or destroyed. Tabs display as one placeholder in this cell profile. */
export function wrapPrompt(text,width) {
 width=Math.max(1,Math.floor(width));const chars=arr(text),rows=[[]],positions=[];
 let row=0,col=0;
 for(let i=0;i<chars.length;i++){
  if(col===width){row++;col=0;rows.push([]);}
  positions[i]={row,col};const ch=chars[i];
  if(ch==='\n'){row++;col=0;rows.push([]);}else {rows[row].push({char:ch,index:i});col++;}
 }
 if(col===width){row++;col=0;rows.push([]);}
 positions[chars.length]={row,col};return {rows,positions};
}
/** Compute prompt geometry AND the scene's available height. Layout is pure.
 * Position maps are shared by weather, caret, paint and hit testing. */
export function promptLayout(doc,width,height) {
 const o=doc.options,mode=doc.mode,vim=mode.startsWith('vim'),full=mode==='vim-full';
 const margin=Math.min(o.margin,Math.max(0,Math.floor((width-12)/2))),border=o.border!=='none'||vim?1:0;
 const w=full||!vim?width-2*margin:Math.min(width-2*margin,o.inlineWidth);
 const numberWidth=vim&&o.lineNumbers?Math.max(3,String(doc.text.split('\n').length).length+1):0;
 const prefix=vim?0:2,innerWidth=Math.max(1,w-2*border-2*o.paddingX-numberWidth-prefix);
 const wrapped=wrapPrompt(doc.text,innerWidth),caretIndex=bounded(doc.caret,0,arr(doc.text).length),at=wrapped.positions[caretIndex];
 const maxAvail=Math.max(1,height-9-2*border-2*o.paddingY-(vim?1:0));
 let visibleRows=mode==='marquee'?1:mode==='grow'?bounded(wrapped.rows.length,Math.min(o.minRows,maxAvail),Math.min(o.maxRows,maxAvail)):full?Math.max(1,height-8-2*o.paddingY):Math.min(maxAvail,Math.max(1,o.inlineRows-2*border-2*o.paddingY-1));
 visibleRows=Math.max(1,visibleRows);
 const h=visibleRows+2*border+2*o.paddingY+(vim?1:0),x=full||!vim?margin:Math.floor((width-w)/2),y=height-2-h;
 const inner={x:x+border+o.paddingX+numberWidth+prefix,y:y+border+o.paddingY,width:innerWidth,height:visibleRows};
 let offset=0,top=0,rows=[],positions=new Map();
 if(mode==='marquee'){
  const chars=arr(doc.text);offset=Math.max(0,caretIndex-innerWidth+1);
  rows=[chars.slice(offset,offset+innerWidth).map((char,j)=>({char:char==='\n'?'↵':char,index:offset+j}))];
  for(let i=offset;i<=Math.min(chars.length,offset+innerWidth);i++)positions.set(i,{x:inner.x+i-offset,y:inner.y});
 }else {
  top=Math.max(0,at.row-visibleRows+1);rows=wrapped.rows.slice(top,top+visibleRows);
  for(let i=0;i<wrapped.positions.length;i++){const p=wrapped.positions[i];if(p.row>=top&&p.row<top+visibleRows)positions.set(i,{x:inner.x+p.col,y:inner.y+p.row-top});}
 }
 const caret=positions.get(caretIndex)??{x:inner.x,y:inner.y};
 // Legacy scene compositions reserved a line at height-4. Reflow their entire
 // scene rectangle by extraRows; both their cells and their hit IDs move together.
 const extraRows=full?0:Math.max(0,h-1),sceneHeight=Math.max(12,height-extraRows);
 return {rect:{x,y,width:w,height:h},inner,rows,positions,caret,offset,top,visibleRows,border,numberWidth,prefix,extraRows,sceneHeight,full,vim};
}
/** In-memory document, undo/redo and Vim-style commands shared by every host.
 * Caller persists snapshot() explicitly. Switching/minimizing/closing cannot
 * erase text. Undo is bounded to 100 edits; document data itself is not evicted. */
export class PromptDocument {
 constructor(text='',options={}){
  this.options=validatePrompt(options);this.mode='marquee';this.normalMode='marquee';this.vimState='normal';this.minimizedMode=null;
  this.text='';this.caret=0;this.anchor=null;this.revision=0;this.undoStack=[];this.redoStack=[];this.register='';this.lineRegister=false;this.pending='';this.count='';this.command='';this.search='';this.message='';this.checkpoint=null;
  this.replace(text,arr(text).length,false);
 }
 configure(patch){const candidate=validatePrompt({...this.options,...patch});if(arr(this.text).length>candidate.maxChars)throw RangeError('maxChars below current draft');this.options=candidate;this.revision++;}
 snapshot(){return {version:1,text:this.text,caret:this.caret,mode:this.mode,normalMode:this.normalMode,vimState:this.vimState,options:{...this.options}};}
 restore(value){if(!value||value.version!==1||typeof value.text!=='string'||!PROMPT_MODES.includes(value.mode)||!Number.isInteger(value.caret))throw RangeError('Draft snapshot');const options=validatePrompt(value.options),chars=arr(value.text);if(chars.length>options.maxChars||value.caret<0||value.caret>chars.length)throw RangeError('Draft bounds');this.options=options;this.replace(value.text,value.caret);this.mode=value.mode;this.normalMode=['marquee','grow'].includes(value.normalMode)?value.normalMode:'marquee';this.vimState=['insert','normal','visual','command'].includes(value.vimState)?value.vimState:'normal';}
 remember(){this.undoStack.push({text:this.text,caret:this.caret});if(this.undoStack.length>100)this.undoStack.shift();this.redoStack=[];}
 replace(text,caret=arr(text).length,history=true){if(typeof text!=='string'||arr(text).length>this.options.maxChars||!Number.isInteger(caret)||caret<0||caret>arr(text).length)throw RangeError('Draft bounds');if(history&&text!==this.text)this.remember();this.text=text;this.caret=caret;this.revision++;}
 setMode(mode){if(!PROMPT_MODES.includes(mode))throw RangeError('Prompt mode');if(['marquee','grow'].includes(mode))this.normalMode=mode;else if(!this.mode.startsWith('vim'))this.vimState='normal';this.mode=mode;this.minimizedMode=null;this.pending='';this.count='';this.revision++;}
 action(action){if(action==='inline')this.setMode('vim-inline');else if(action==='full')this.setMode('vim-full');else if(action==='maximize')this.setMode(this.mode==='vim-full'?'vim-inline':'vim-full');else if(action==='minimize'){if(this.mode.startsWith('vim')){this.minimizedMode=this.mode;this.mode=this.normalMode;}}else if(action==='restore'){this.setMode(this.minimizedMode??'vim-inline');}else if(action==='close'){this.mode=this.normalMode;this.vimState='normal';this.minimizedMode=null;this.anchor=null;this.command='';this.pending='';}else throw RangeError('Prompt action');this.revision++;}
 bounds(){const c=arr(this.text);let start=this.caret,end=this.caret;while(start>0&&c[start-1]!=='\n')start--;while(end<c.length&&c[end]!=='\n')end++;return {start,end};}
 selection(){if(this.anchor===null||(this.anchor===this.caret&&this.vimState!=='visual'))return null;return [Math.min(this.anchor,this.caret),Math.min([...this.text].length,Math.max(this.anchor,this.caret)+(this.vimState==='visual'?1:0))];}
 insert(text){let c=arr(this.text),start=this.caret,end=start;const sel=this.selection();if(sel){[start,end]=sel;}this.replace(c.slice(0,start).join('')+text+c.slice(end).join(''),start+arr(text).length);this.anchor=null;}
 erase(start,end){const c=arr(this.text);start=bounded(start,0,c.length);end=bounded(end,start,c.length);this.replace(c.slice(0,start).join('')+c.slice(end).join(''),start);}
 undo(){const state=this.undoStack.pop();if(!state)return;this.redoStack.push({text:this.text,caret:this.caret});this.text=state.text;this.caret=state.caret;this.anchor=null;this.revision++;}
 redo(){const state=this.redoStack.pop();if(!state)return;this.undoStack.push({text:this.text,caret:this.caret});this.text=state.text;this.caret=state.caret;this.anchor=null;this.revision++;}
 vertical(delta){const c=arr(this.text),{start,end}=this.bounds(),col=this.caret-start;let pos=this.caret;for(let j=0;j<Math.abs(delta);j++){this.caret=pos;const b=this.bounds();if(delta<0){if(!b.start){pos=0;break;}let s=b.start-1;while(s>0&&c[s-1]!=='\n')s--;pos=Math.min(b.start-1,s+col);}else{if(b.end===c.length){pos=c.length;break;}let e=b.end+1;while(e<c.length&&c[e]!=='\n')e++;pos=Math.min(e,b.end+1+col);}}this.caret=pos;}
 word(direction,endWord=false){const c=arr(this.text),word=ch=>ch&&/[\p{L}\p{N}_]/u.test(ch);let p=this.caret;if(direction<0){p=Math.max(0,p-1);while(p>0&&!word(c[p]))p--;while(p>0&&word(c[p-1]))p--;}else{if(endWord)p=Math.min(c.length,p+1);if(!endWord)while(p<c.length&&word(c[p]))p++;while(p<c.length&&!word(c[p]))p++;if(endWord)while(p+1<c.length&&word(c[p+1]))p++;}this.caret=p;}
 /** Executes the supported Ex subset. :q and even :q! close the VIEW, never
  * destroy the shared draft. :w creates an in-memory checkpoint, not a file. */
 ex(command){const cmd=command.replace(/^:/,'').trim();this.message='';if(['q','q!','wq','x'].includes(cmd)){if(cmd==='wq'||cmd==='x')this.checkpoint=this.snapshot();this.action('close');}else if(cmd==='w'){this.checkpoint=this.snapshot();this.message='Checkpoint retained in memory; Export saves to a file.';}else if(cmd==='undo')this.undo();else if(cmd==='redo')this.redo();else if(cmd==='set number'||cmd==='set nu')this.configure({lineNumbers:true});else if(cmd==='set nonumber'||cmd==='set nonu')this.configure({lineNumbers:false});else if(cmd==='help')this.message='i a o / h j k l w b e 0 $ gg G / dd yy p x u Ctrl-R / :w :q :set number. Close never discards.';else if(/^\d+$/.test(cmd)){const n=Number(cmd);const lines=this.text.split('\n');this.caret=arr(lines.slice(0,Math.max(0,Math.min(lines.length-1,n-1))).join('\n')).length+(n>1&&lines.length>1?1:0);}else this.message='Unsupported command: '+cmd;this.command='';this.vimState='normal';this.pending='';this.revision++;}
 /** Return true only when the editor consumed the key. key uses DOM names; ctrl,
  * alt, shift, meta are booleans. Ctrl-A/E are document endpoints in all modes. */
 key(event){const {key,ctrl=false,alt=false,meta=false,shift=false}=event;const c=arr(this.text),vim=this.mode.startsWith('vim');
  if(ctrl&&key.toLowerCase()==='a'){this.caret=0;this.revision++;return true;}
  if(ctrl&&key.toLowerCase()==='e'){this.caret=c.length;this.revision++;return true;}
  if(ctrl&&key.toLowerCase()==='r'&&vim){this.redo();return true;}
  if(ctrl&&key.toLowerCase()==='z'&&!vim){shift?this.redo():this.undo();return true;}
  if(ctrl||alt||meta)return false;
  if(vim&&this.vimState==='command'){
   if(key==='Escape'){this.command='';this.vimState='normal';}else if(key==='Enter'){const command=this.command;if(command.startsWith('/')){this.search=command.slice(1);this.findNext();this.vimState='normal';this.command='';}else this.ex(command);}else if(key==='Backspace')this.command=arr(this.command).slice(0,-1).join('');else if(arr(key).length===1&&this.command.length<256)this.command+=key;this.revision++;return true;
  }
  if(vim&&key==='Escape'){this.vimState='normal';this.anchor=null;this.pending='';this.count='';this.revision++;return true;}
  if(!vim||this.vimState==='insert'){
   if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(key)){if(shift&&this.anchor===null)this.anchor=this.caret;if(!shift)this.anchor=null;}
   if(['Backspace','Delete'].includes(key)&&this.selection()){const bounds=this.selection();this.anchor=null;this.erase(...bounds);return true;}
   if(key==='ArrowLeft')this.caret=Math.max(0,this.caret-1);else if(key==='ArrowRight')this.caret=Math.min(c.length,this.caret+1);else if(key==='ArrowUp')this.vertical(-1);else if(key==='ArrowDown')this.vertical(1);else if(key==='Home')this.caret=this.bounds().start;else if(key==='End')this.caret=this.bounds().end;else if(key==='Backspace'){if(this.caret)this.erase(this.caret-1,this.caret);}else if(key==='Delete')this.erase(this.caret,this.caret+1);else if(key==='Enter'&&(vim||this.mode==='grow'||shift))this.insert('\n');else if(key==='Tab'&&vim)this.insert('  ');else if(arr(key).length===1)this.insert(key);else return false;this.revision++;return true;
  }
  if(/^[1-9]$/.test(key)||key==='0'&&this.count){this.count=(this.count+key).slice(0,3);return true;}
  let repeat=Math.min(999,Number(this.count)||1);this.count='';if(this.pending)repeat=Math.min(999,repeat*(this.pendingCount||1));
  if(this.pending){const p=this.pending;this.pending='';if(p==='g'&&key==='g')this.caret=0;else if(p===key&&['d','y','c'].includes(p)){let {start,end}=this.bounds();for(let n=1;n<repeat&&end<c.length;n++){end++;while(end<c.length&&c[end]!=='\n')end++;}end=Math.min(c.length,end+1);this.register=c.slice(start,end).join('');this.lineRegister=true;if(p!=='y')this.erase(start,end);if(p==='c')this.vimState='insert';}else if(['d','c','y'].includes(p)&&['w','$','e'].includes(key)){const start=this.caret;if(key==='$')this.caret=this.bounds().end;else this.word(1,key==='e');const end=this.caret+(key==='e'?1:0);this.register=c.slice(start,end).join('');this.lineRegister=false;this.caret=start;if(p!=='y')this.erase(start,end);if(p==='c')this.vimState='insert';}this.revision++;return true;}
  const selected=this.selection();
  if(this.vimState==='visual'&&['d','x','y','c'].includes(key)){if(selected){this.register=c.slice(...selected).join('');this.lineRegister=false;this.anchor=null;if(key!=='y')this.erase(...selected);}this.vimState=key==='c'?'insert':'normal';return true;}
  for(let n=0;n<repeat;n++){
   if(['h','ArrowLeft'].includes(key))this.caret=Math.max(0,this.caret-1);else if(['l','ArrowRight'].includes(key))this.caret=Math.min(c.length,this.caret+1);else if(['j','ArrowDown'].includes(key))this.vertical(1);else if(['k','ArrowUp'].includes(key))this.vertical(-1);else if(key==='w')this.word(1);else if(key==='b')this.word(-1);else if(key==='e')this.word(1,true);else if(key==='0'||key==='Home')this.caret=this.bounds().start;else if(key==='$'||key==='End')this.caret=this.bounds().end;else if(key==='G')this.caret=c.length;
   else if(['d','y','c','g'].includes(key)){this.pending=key;this.pendingCount=repeat;break;}else if(key==='i')this.vimState='insert';else if(key==='a'){this.caret=Math.min(c.length,this.caret+1);this.vimState='insert';}else if(key==='I'){this.caret=this.bounds().start;this.vimState='insert';}else if(key==='A'){this.caret=this.bounds().end;this.vimState='insert';}else if(key==='o'){this.caret=this.bounds().end;this.insert('\n');this.vimState='insert';}else if(key==='O'){this.caret=this.bounds().start;this.insert('\n');this.caret--;this.vimState='insert';}else if(key==='x')this.erase(this.caret,this.caret+1);else if(key==='D'||key==='C'){this.erase(this.caret,this.bounds().end);if(key==='C')this.vimState='insert';}else if(key==='u')this.undo();else if(key==='v'){this.anchor=this.caret;this.vimState='visual';}else if(key==='V'){const b=this.bounds();this.anchor=b.start;this.caret=b.end;this.vimState='visual';}else if(key==='p'||key==='P'){if(this.lineRegister){const b=this.bounds();this.caret=key==='P'?b.start:Math.min(c.length,b.end+1);const prefix=key==='p'&&b.end===c.length&&!this.register.startsWith('\n')?'\n':'';this.insert(prefix+this.register);}else{if(key==='p')this.caret=Math.min(c.length,this.caret+1);this.insert(this.register);}}else if(key===':'||key==='/'){this.command=key;this.vimState='command';}else if(key==='n')this.findNext();else {this.message='Unmapped Vim-style key: '+key;break;}
  }
  this.revision++;return true;
 }
 findNext(){if(!this.search)return;const c=arr(this.text),needle=arr(this.search);for(let step=1;step<=c.length;step++){const i=(this.caret+step)%(c.length||1);if(c.slice(i,i+needle.length).join('')===this.search){this.caret=i;return;}}this.message='Pattern not found';}
}
