import {RestorationModel,RESTORATION_SCENES} from './restoration-model.js';
import {RestorationRenderer} from './restoration-renderer.js';
import {PromptDocument,promptLayout,DEFAULT_PROMPT} from './prompt.js';
import {ChangeTrack,BORDER_GLYPHS,decoratedInk,validateDecoration,gradientInk,paintStyled} from './styles.js';
import {paintInkWeather} from './continuity-ink.js';
import {signedWheel,textInsertions,viewDisplacement} from './continuity-input.js';
import {Projector} from './black-hole-space.js';
import {clamp,rgb,mixColor,flattened} from './observatory.js';
import {activateBlackHole} from './black-hole-renderer.js';
export const PROMPT_IDS={body:910001,minimize:910002,maximize:910003,close:910004,restore:910005,resize:910006};
export const WORKBENCH_SCENES=RESTORATION_SCENES;

/** Pointer navigation is independent of opt-in unmodified keyboard navigation. */
export const WORKBENCH_SPATIAL_SCENES = Object.freeze([
 'warp','black-hole','infinite','world-weather','dag','graph-explorer','git-history',
 'spatial-menu','windows','shapes','fleet-room','impossible','waterfall','tarmac',
 'ocean','dunes','model-viewer'
]);
/** Only the node inspector is a nonmodal panel; arbitrary drawers stay modal. */
export function workbenchNodeInspector(model) {
 return model.modalStack.peek()?.id === 'node' && model.modalContext === 'node' &&
  ['dag','graph-explorer','git-history','spatial-menu'].includes(model.scene);
}
/** True when a top-level overlay owns the entire scene input plane. */
export function workbenchSceneBlocked(model) {
 return !!model.modalStack.peek() ? !workbenchNodeInspector(model) : !!model.showPalette;
}
function pointerInRect(x,y,r) {
 return !!r && x>=r.x && y>=r.y && x<r.x+r.width && y<r.y+r.height;
}
/** Classify a pointer using the current rendered hit map. Pure, no effects/time.
 * Coordinates and displacement are in terminal cells, not CSS/device pixels.
 * Returns a gesture kind, or action/blocked/none. Invalid coordinates reject.
 * Example: workbenchPointerIntent(model,view,20,12,{shiftKey:true}).
 */
export function workbenchPointerIntent(model,view,x,y,options={}) {
 if(!Number.isFinite(x)||!Number.isFinite(y))throw new RangeError('Finite pointer coordinates required');
 const f=view?.frame,button=options.button??0;
 if(!f||x<0||y<0||x>=f.width||y>=f.height)return {kind:'none'};
 if(button!==0&&button!==2)return {kind:'blocked'};
 const id=f.cells[(Math.floor(y)*f.width+Math.floor(x))*4+3];
 const action=view.actions?.[id];
 const gesture={scene:model.scene,promptMode:model.document.mode,width:f.width,height:f.height};
 const actionIntent=()=>({...gesture,kind:'action',actionId:id});
 const overlayIds=new Set((view.modalSemantics??[]).map(s=>s.id));
 if(workbenchSceneBlocked(model)) {
  // Scene palette is exclusive too; its actions have already replaced the scene's.
  return button===0&&action&&(model.showPalette&&!model.modalStack.peek()||overlayIds.has(id))
   ? actionIntent():{kind:'blocked'};
 }
 if(pointerInRect(x,y,view.pointerOverlay))
  return button===0&&action&&overlayIds.has(id)?actionIntent():{kind:'blocked'};
 const spatial=WORKBENCH_SPATIAL_SCENES.includes(model.scene);
 // The prompt is an editor, never a camera surface, even on right-button down.
 if(pointerInRect(x,y,view.prompt?.rect)) {
  if(button!==0)return {kind:'blocked'};
  if(id===PROMPT_IDS.body)return {...gesture,kind:'prompt-selection'};
  if(id===PROMPT_IDS.resize)return {...gesture,kind:'prompt-resize'};
  return action?.kind==='prompt'?actionIntent():{kind:'blocked'};
 }
 if(button===2)return spatial?{...gesture,kind:'pan'}:{kind:'none'};
 if(action?.kind==='select-window')
  return {...gesture,kind:options.altKey?'window-rotate':'window',windowId:action.value};
 if(action)return actionIntent();
 // A painted rule/header with no semantic action is still a scene surface.
 // There is deliberately NO click-weather fallback in any workshop.
 return spatial?{...gesture,kind:options.shiftKey||model.camera.snapshot().mode==='pan'?'pan':'look'}:{kind:'none'};
}
/** Begin one host gesture. Only actions/selection commit here; camera transforms
 * happen on move, and no synthetic click is dispatched at the end of a drag. */
export function beginWorkbenchPointer(model,view,x,y,options={}) {
 const intent=workbenchPointerIntent(model,view,x,y,options);
 if(intent.kind==='action')activateWorkbench(model,intent.actionId,view);
 else if(intent.kind==='prompt-selection')model.promptCaretAt(x,y,!!options.shiftKey);
 else if(intent.kind==='window'||intent.kind==='window-rotate')model.spaceWindows.select(intent.windowId);
 return intent;
}
/** Apply a captured gesture in cell units. Returns false after scene/layout/mode
 * ownership changes or a blocking overlay opens. Hosts release on up/cancel/blur.
 * target optionally supplies absolute {x,y} for an editor selection drag.
 */
export function moveWorkbenchPointer(model,intent,dx,dy,target) {
 if(![dx,dy].every(Number.isFinite))throw new RangeError('Finite pointer displacement required');
 if(!intent||intent.scene!==model.scene||workbenchSceneBlocked(model)||
    intent.promptMode!==model.document.mode||intent.width!==model.width||intent.height!==model.height)return false;
 if(target&&(!Number.isFinite(target.x)||!Number.isFinite(target.y)))throw new RangeError('Finite selection point required');
 const c=model.camera.snapshot();
 switch(intent.kind){
  case 'prompt-selection':if(target)model.promptCaretAt(target.x,target.y,true);break;
  case 'prompt-resize':model.resizePrompt(dx,dy);break;
  case 'window':model.moveWindowByScreen(intent.windowId,dx,dy);break;
  case 'window-rotate':{
   const w=model.spaceWindows.list().find(w=>w.id===intent.windowId);if(!w)return false;
   model.spaceWindows.move(w.id,{yaw:clamp(w.yaw+dx*2.4,-170,170),pitch:clamp(w.pitch-dy*4.8,-89,89)});break;
  }
  case 'pan':model.panBy(-dx*.5,dy,0);break;
  case 'look':model.lookBy(clamp(dx*c.sensitivity*8,-720,720),clamp(-dy*c.sensitivity*16,-720,720));break;
  default:return false;
 }
 return true;
}
/** Wheel on the currently displayed scene, not through editor/overlay surfaces. */
export function wheelWorkbenchPointer(model,view,x,y,sample) {
 const intent=workbenchPointerIntent(model,view,x,y,{button:2});
 if(intent.kind!=='pan')return false;
 model.wheel(sample);return true;
}

/** RC2 controller: one document owns all prompt modes. Existing scene controllers
 * are delegated to, not replaced. Both DOM and terminal hosts use promptKey(). */
export class WorkbenchModel extends RestorationModel {
 constructor(){super();this.managedPrompt=true;this.edition='v0.9.0-rc.2';this.document=new PromptDocument(this.draft);this.decoration=validateDecoration();this.changeTrack=new ChangeTrack();this.changeTrack.update(67,0);this.showChangeTrack=false;this.showDecoration=false;}
 setScene(id){super.setScene(id);if(typeof this.notice==='string'&&this.notice.endsWith(' / v0.9.0-rc.1'))this.notice=this.notice.slice(0,-'v0.9.0-rc.1'.length)+'v0.9.0-rc.2';}
 /** A stacked modal restores its parent's context and keyboard selection on close. */
 openModal(kind='center',context='commands'){
  const parent={context:this.modalContext,query:this.modalQuery,selected:this.modalSelected};
  try{super.openModal(kind,context);}catch(error){
   this.modalContext=parent.context;this.modalQuery=parent.query;this.modalSelected=parent.selected;throw error;
  }
  this.modalStack.items[this.modalStack.items.length-1].returnContext=parent;
 }
 dismissModal(){
  if(workbenchNodeInspector(this)){this.clearGraphFocus();return true;}
  const top=this.modalStack.peek();if(!this.modalStack.dismiss())return false;
  const parent=top.returnContext;
  if(parent){this.modalContext=parent.context;this.modalQuery=parent.query;this.modalSelected=parent.selected;}
  else if(this.modalStack.peek()?.id==='node')this.modalContext='node';
  this.revision++;return true;
 }
 wheel(sample){
  const pixels=signedWheel(sample);
  if(!pixels||workbenchSceneBlocked(this))return;
  if(!WORKBENCH_SPATIAL_SCENES.includes(this.scene))return super.wheel(sample);
  const amount=clamp(pixels/100,-4,4);
  if(sample.shiftKey&&['windows','shapes','fleet-room'].includes(this.scene))
   this.moveWindowByScreen(this.spaceWindows.selected,0,0,amount*2);
  else if(this.scenicMode==='world'&&['waterfall','tarmac','black-hole','ocean','dunes','model-viewer'].includes(this.scene)&&this.worldView.projection===1){
   this.worldView.span=clamp(this.worldView.span*Math.exp(amount*.08),16,400);this.revision++;
  }else this.editCamera(()=>this.camera.dolly(-amount*2));
 }
 promptLayout(){return promptLayout(this.document,this.width,this.height);}
 draftView(){if(!this.document)return super.draftView();const l=this.promptLayout();return {text:l.rows.map(r=>r.map(g=>g.char).join('')).join('\n'),row:l.inner.y,originX:l.inner.x,offset:l.offset,capacity:l.inner.width,cursorX:l.caret.x};}
 syncDocument(previous){this.draft=this.document.text;this.draftCaret=this.document.caret;const l=this.promptLayout();if(this.inputWeather.enabled&&this.options.weatherIntensity>0){for(const g of textInsertions(previous,this.draft)){const p=l.positions.get(g.index);if(!p||/\s/.test(g.glyph))continue;this.inkEvents.push(Object.freeze({id:++this.inkSerial,space:'screen',x:p.x,y:p.y,glyph:g.glyph,atMs:this.motionMs,...this.inputWeather,hue:(this.inkSerial*137.508)%360}));}this.inkEvents=this.inkEvents.filter(e=>this.motionMs-e.atMs<e.lifeMs).slice(-96);}this.revision++;}
 replaceDraft(text,caret){if(!this.document)return super.replaceDraft(text,caret);const previous=this.document.text;this.document.replace(text,caret??[...text].length);this.syncDocument(previous);}
 input(text){const previous=this.document.text;this.document.insert(text);this.syncDocument(previous);}
 backspace(){this.promptKey({key:'Backspace'});}
 setDraftCaret(index){if(!this.document)return super.setDraftCaret(index);if(!Number.isInteger(index)||index<0||index>[...this.document.text].length)throw RangeError('Scalar caret');this.document.caret=index;this.draftCaret=index;this.revision++;}
 promptKey(event){const previous=this.document.text,handled=this.document.key({...event,ctrl:event.ctrl??event.ctrlKey??false,alt:event.alt??event.altKey??false,meta:event.meta??event.metaKey??false,shift:event.shift??event.shiftKey??false});if(handled)this.syncDocument(previous);return handled;}
 configurePrompt(patch){this.document.configure(patch);this.revision++;}
 promptMode(mode){this.document.setMode(mode);this.navEnabled=false;this.revision++;}
 promptAction(action){this.document.action(action);this.navEnabled=false;this.revision++;}
 promptCaretAt(x,y,extend=false){this.navEnabled=false;const l=this.promptLayout();let best=this.document.caret,d=Infinity;for(const [i,p]of l.positions){const distance=Math.abs(p.y-y)*1000+Math.abs(p.x-x);if(distance<d){d=distance;best=i;}}if(extend&&this.document.anchor===null)this.document.anchor=this.document.caret;if(!extend)this.document.anchor=null;this.setDraftCaret(best);}
 moveWindowByScreen(id,dx,dy,forward=0){if(![dx,dy,forward].every(Number.isFinite))throw RangeError('Window displacement');const w=this.spaceWindows.list().find(w=>w.id===id);if(!w)throw RangeError('Unknown window');const c=this.camera.snapshot(),p=new Projector(c,this.width,this.promptLayout().sceneHeight),q=p.project(w),d=Math.max(1,q?.z??40),v=viewDisplacement(c,dx*d/p.focal,-dy*2*d/p.focal,forward);this.spaceWindows.move(id,{x:w.x+v.x,y:w.y+v.y,z:w.z+v.z});this.revision++;}
 resizePrompt(dx,dy){const o=this.document.options;this.configurePrompt({inlineWidth:Math.round(clamp(o.inlineWidth+dx,24,240)),inlineRows:Math.round(clamp(o.inlineRows+dy,5,80))});}
 send(){if(!this.draft.trim())return;this.messages.push({id:++this.serial,text:'YOU: '+this.draft,atMs:this.motionMs,local:true});if(this.messages.length>256)this.messages.shift();this.document.replace('',0);this.draft='';this.draftCaret=0;this.revision++;}
 updateValue(value){this.changeTrack.update(value,this.motionMs);this.showChangeTrack=true;this.revision++;}
}
function cell(f,x,y,glyph,fg,bg,id){x=Math.round(x);y=Math.round(y);if(x<0||y<0||x>=f.width||y>=f.height)return;const k=(y*f.width+x)*4;f.cells[k]=glyph.codePointAt(0);f.cells[k+1]=fg;if(bg!==undefined)f.cells[k+2]=bg;f.cells[k+3]=id??0;}
/** Alpha composition order: scene and weather -> translucent prompt surface ->
 * full-opacity text. It never treats text foreground as part of the background. */
export function paintPrompt(frame,doc,timeMs,engine){
 const l=promptLayout(doc,frame.width,frame.height),o=doc.options,bg=rgb(o.background),ink=rgb(o.foreground),accent=rgb(o.accent),r=l.rect,selection=doc.selection();
 for(let y=r.y;y<r.y+r.height;y++)for(let x=r.x;x<r.x+r.width;x++){
  const k=(y*frame.width+x)*4,g=frame.cells[k];
  const decorative=[32,0x2580,0x2584,0x258c,0x2590].includes(g)||(g>=0x2800&&g<=0x28ff);
  if(!decorative)frame.cells[k]=32;
  frame.cells[k+1]=mixColor(frame.cells[k+1],bg,o.alpha);
  frame.cells[k+2]=mixColor(frame.cells[k+2],bg,o.alpha);
  frame.cells[k+3]=PROMPT_IDS.body;
 }
 function write(x,y,s,color=ink,id=PROMPT_IDS.body){for(const ch of s){if(x>=r.x+r.width-1)break;const k=(y*frame.width+x)*4;if(k>=0&&k+3<frame.cells.length)cell(frame,x,y,ch,color,flattened(frame,k),id);x++;}}
 const borders=BORDER_GLYPHS[l.vim&&o.border==='none'?'rounded':o.border];
 if(l.border){const [tl,tr,bl,br,h,v]=borders;for(let x=r.x+1;x<r.x+r.width-1;x++){write(x,r.y,h,accent);write(x,r.y+r.height-1,h,accent);}for(let y=r.y+1;y<r.y+r.height-1;y++){cell(frame,r.x,y,v,accent,flattened(frame,(y*frame.width+r.x)*4),PROMPT_IDS.body);cell(frame,r.x+r.width-1,y,v,accent,flattened(frame,(y*frame.width+r.x+r.width-1)*4),PROMPT_IDS.body);}[[r.x,r.y,tl],[r.x+r.width-1,r.y,tr],[r.x,r.y+r.height-1,bl],[r.x+r.width-1,r.y+r.height-1,br]].forEach(([x,y,g])=>cell(frame,x,y,g,accent,flattened(frame,(y*frame.width+x)*4),PROMPT_IDS.body));}
 const semantics=[],actions={};
 function button(id,x,y,label,description,color){for(let j=0;j<label.length;j++){const xx=x+j,k=(y*frame.width+xx)*4;if(xx<r.x+r.width-1)cell(frame,xx,y,label[j],color,flattened(frame,k),id);}semantics.push({id,label:description});actions[id]={kind:'prompt',value:description};}
 if(l.vim){write(r.x+2,r.y,(' VIM MODE · '+doc.vimState.toUpperCase()+' ').slice(0,Math.max(0,r.width-21)),accent);const bx=r.x+r.width-17;button(PROMPT_IDS.minimize,bx,r.y,'[ - ]','minimize',0xdcc17e);button(PROMPT_IDS.maximize,bx+5,r.y,l.full?'[ ◇ ]':'[ □ ]','maximize',0x8ccfc4);button(PROMPT_IDS.close,bx+10,r.y,'[ × ]','close',0xe2a4ad);
  const status=doc.vimState==='command'?doc.command:(doc.message||'Esc NORMAL · i INSERT · :w checkpoint · :q close view · drag ↘ resize');write(r.x+2,r.y+r.height-2,status,accent);
  button(PROMPT_IDS.resize,r.x+r.width-3,r.y+r.height-1,'↘ ','resize',accent);
 }else if(doc.minimizedMode){button(PROMPT_IDS.restore,r.x+2,r.y,'[ VIM restore ]','restore',accent);}
 else if(l.border)write(r.x+2,r.y,' '+(doc.mode==='grow'?'GROWING PROMPT':'SCROLLING PROMPT')+' ',accent);
 for(let row=0;row<l.rows.length;row++){
  if(l.numberWidth)write(l.inner.x-l.numberWidth,l.inner.y+row,String(l.top+row+1).padStart(l.numberWidth-1)+' ',0x83929e);
  if(l.prefix&&row===0)write(l.inner.x-2,l.inner.y,'> ',accent);
  for(let col=0;col<l.rows[row].length;col++){
   const g=l.rows[row][col],x=l.inner.x+col,y=l.inner.y+row,k=(y*frame.width+x)*4;let color=ink;
   if(o.hueStep||o.hueSpeed){color=decoratedInk(engine,{...o,state:'active',activeColor:o.foreground,animate:'active',periodMs:o.huePeriodMs},g.index,timeMs);}
   let background=flattened(frame,k);if(selection&&g.index>=selection[0]&&g.index<selection[1])background=mixColor(background,rgb(o.selectionColor),.8);
   const shown=/[\x00-\x1f\x7f]/.test(g.char)?' ':g.char;cell(frame,x,y,shown,color,background,PROMPT_IDS.body);
  }
 }
 // Cursor is an attribute of its existing cell; never replace the typed glyph.
 if(doc.options.active){const {x,y}=l.caret,k=(y*frame.width+x)*4;if(k>=0&&k+3<frame.cells.length){const existing=frame.cells[k];if(existing===32||existing===0x2580||existing>=0x2800&&existing<=0x28ff)cell(frame,x,y,'▏',accent,flattened(frame,k),PROMPT_IDS.body);else frame.cells[k+2]=mixColor(frame.cells[k+2],accent,.18);}}
 return {layout:l,semantics,actions};
}
/** RC2 scene compositor. Earlier models retain their byte-identical entry points.
 * All scene hit IDs are rendered in the reflowed viewport, not translated with a
 * stale hit map. A fullscreen editor overlays; bounded prompts reserve space. */
export class WorkbenchRenderer extends RestorationRenderer {
 // Modal ownership is deferred until after the editor, including fullscreen.
 modal(view,model){if(!model.managedPrompt)super.modal(view,model);}
 render(model,atMs=model.dataMs){if(!(model instanceof WorkbenchModel))return super.render(model,atMs);
  const layout=model.promptLayout(),proxy=Object.create(model);proxy.height=layout.sceneHeight;proxy.inkEvents=[];proxy.showPalette=false;
  const view=super.render(proxy,atMs);let frame=view.frame;
  if(frame.height!==model.height){
   const canvas=this.background(model,model.effective());
   // Background extends underneath the prompt; the reflowed scene stops at the
   // exact new boundary. This prevents both content and its hit targets overdraw.
   const rows=Math.max(0,Math.min(layout.rect.y,frame.height));canvas.cells.set(frame.cells.subarray(0,rows*frame.width*4));frame=canvas;
  }
  paintInkWeather(frame,model.inkEvents,model.motionMs,h=>this.ink(h));
  if(model.showChangeTrack){const state=model.changeTrack.sample(model.motionMs,this.engine),label='LIVE VALUE  '+model.changeTrack.value;for(let i=0;i<label.length;i++)cell(frame,4+i,6,label[i],gradientInk(this.engine,state.colors,i,model.motionMs,state),undefined,0);}
  if(model.showDecoration){
   frame=paintStyled(this.engine,frame,[{kind:'box',id:920001,x:3,y:3,width:Math.min(frame.width-6,70),height:7},{kind:'text',id:920002,x:5,y:5,width:Math.min(frame.width-10,64),height:3,text:'DECORATED SURFACE / active selection'}],model.decoration,model.motionMs);
  }
  // Only the current host owns this edition label; archived rendering stays unchanged.
  if(layout.rect.y>1){const title='NOCTURNE / WORKBENCH v0.9.0-rc.2  '+String(model.scene).toUpperCase();for(let x=0;x<frame.width;x++)cell(frame,x,1,title[x]||' ',0xd6ccbc,0x0c1119,0);}
  const prompt=paintPrompt(frame,model.document,model.motionMs,this.engine);
  const visible=new Set();for(let i=3;i<frame.cells.length;i+=4)if(frame.cells[i])visible.add(frame.cells[i]);
  const result={...view,frame,semantics:[...view.semantics.filter(s=>visible.has(s.id)),...prompt.semantics],actions:{...Object.fromEntries(Object.entries(view.actions).filter(([id])=>visible.has(+id))),...prompt.actions},prompt:prompt.layout};
  if(model.modalStack.peek()){
   const underneath={semantics:result.semantics,actions:result.actions};
   const firstOverlayNode=result.nodes.length;
   super.modal(result,model);
   // Input ownership uses the same animated rectangle that was actually painted.
   const box=result.nodes.slice(firstOverlayNode).find(n=>n.id===49999);
   if(box)result.pointerOverlay={x:box.x,y:box.y,width:box.width,height:box.height};
   result.modalSemantics=[...result.semantics];
   if(workbenchNodeInspector(model)){
    const exposed=new Set();
    for(let i=3;i<result.frame.cells.length;i+=4){
     const index=(i-3)/4,x=index%result.frame.width,y=Math.floor(index/result.frame.width);
     if(!pointerInRect(x,y,result.pointerOverlay))exposed.add(result.frame.cells[i]);
    }
    const sceneActions=Object.fromEntries(Object.entries(underneath.actions).filter(([id])=>exposed.has(+id)));
    result.actions={...sceneActions,...result.actions};
    result.semantics=[...underneath.semantics.filter(s=>exposed.has(s.id)),...result.modalSemantics];
   }
  }
  else if(model.showPalette){
   const width=Math.min(76,frame.width-6),x=Math.floor((frame.width-width)/2),rows=WORKBENCH_SCENES.filter(s=>s.name.toLowerCase().includes(model.paletteQuery.toLowerCase())).slice(0,Math.min(14,frame.height-12));
   const nodes=[{kind:'box',id:92999,x,y:4,width,height:rows.length+6,text:' SCENE PALETTE ',fg:0x99bfb7,bg:0x101721,bgOpacity:950},{kind:'text',x:x+2,y:6,width:width-4,height:1,text:'> '+model.paletteQuery,fg:0xd6ccbc}];result.semantics=[];result.actions={};
   rows.forEach((r,i)=>{const id=92500+i;nodes.push({kind:'item',id,x:x+2,y:8+i,width:width-4,height:1,text:r.name,fg:0xd6ccbc,bg:0x223845,bgOpacity:950,state:i===model.selected?2:0});result.semantics.push({id,label:r.name});result.actions[id]={kind:'scene',value:r.id};});result.frame=this.engine.paint(result.frame,model.motionMs,nodes);
  }
  return result;
 }
}
export function activateWorkbench(model,id,view){const action=view.actions[id];if(action?.kind==='prompt'){if(action.value!=='resize')model.promptAction(action.value);return;}activateBlackHole(model,id,view);}
