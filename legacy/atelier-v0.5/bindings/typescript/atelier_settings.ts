/** Versioned visual settings, not transcript/session restore. Loading validates
 * into an independent model first. A host swaps the returned model atomically.
 * No local draft, provider record, filesystem path or credential is exported. */
import {AtelierModel,ATELIER_SCENES} from './atelier.js';
import {clamp,finite,rgb} from './observatory.js';
import {WindowManager,windowOptions} from './window_fx.js';
import {validateGraph,layoutOptions} from './spatial.js';
const plain=(v:unknown):Record<string,unknown>=>{if(!v||typeof v!=='object'||Array.isArray(v))throw new RangeError('Expected a settings object');return v as Record<string,unknown>;};
/** Return owned JSON-safe settings. Window motions are normalized to intent,
 * so reopening settings starts at settled visibility rather than an old clock.
 * Example: JSON.stringify(exportAtelierSettings(model), null, 2). */
export function exportAtelierSettings(m:AtelierModel):Record<string,unknown>{return JSON.parse(JSON.stringify({version:5,scene:m.scene,view:{width:m.width,height:m.height},options:m.options,palette:m.palette,camera:m.camera.snapshot(),cameraMode:m.cameraMode,flightSpeed:m.flightSpeed,textConfig:m.textConfig,textValue:m.textValue,particleConfig:m.particleConfig,windowOptions:m.workspace.options,selectedWindow:m.workspace.selected,windows:m.workspace.windows.map(w=>({title:w.title,x:w.x,y:w.y,width:w.width,height:w.height,shape:w.shape,depth:w.depth,yaw:w.yaw,pitch:w.pitch,roll:w.roll,mode:w.mode,maximized:w.maximized,rolled:w.rolled,alpha:w.fade.to})),graph:m.graph,layoutConfig:m.layoutConfig,selectedNode:m.selectedNode}));}
/** Validate all settings and create an owned model at time zero. Throws on
 * invalid versions/ranges/IDs/masks; caller state is untouched on failure.
 * Layout is solved with fixed iterations. For large force imports, call this
 * in a worker or use GraphLayoutJob in the host. Bounded to 256 graph nodes. */
export function loadAtelierSettings(value:unknown):AtelierModel{
 const d=plain(value);if(d.version!==5)throw new RangeError('Spatial Atelier settings version must be 5');const m=new AtelierModel();
 if(typeof d.scene!=='string'||!ATELIER_SCENES.some(s=>s.id===d.scene))throw new RangeError('Unknown scene');
 const view=plain(d.view);const width=finite(view.width,36,240,'columns'),height=finite(view.height,18,100,'rows');if(!Number.isInteger(width)||!Number.isInteger(height))throw new RangeError('Integer viewport required');m.resize(width,height);m.setScene(d.scene);
 m.configure(plain(d.options));m.configureText(plain(d.textConfig));m.setDisplayText(String(d.textValue??''));m.configureParticles(plain(d.particleConfig));
 const p=plain(d.palette);if(typeof p.id!=='string'||p.id.length>80||typeof p.name!=='string'||p.name.length>120||!Array.isArray(p.colors)||p.colors.length<1||p.colors.length>32)throw new RangeError('Invalid palette');p.colors.forEach(c=>rgb(String(c)));rgb(String(p.background));rgb(String(p.ink));m.palette=JSON.parse(JSON.stringify(p)) as typeof m.palette;
 m.graph=validateGraph(d.graph as Parameters<typeof validateGraph>[0]);m.beginLayout(layoutOptions(plain(d.layoutConfig)),m.graph);while(!m.stepLayout()){}if(typeof d.selectedNode==='string'&&m.graph.nodes.some(n=>n.id===d.selectedNode))m.selectedNode=d.selectedNode;
 const camera=plain(d.camera),target=plain(camera.target);m.camera.target={x:finite(target.x,-10000,10000,'target x'),y:finite(target.y,-10000,10000,'target y'),z:finite(target.z,-10000,10000,'target z')};for(const [k,lo,hi] of [['yaw',-180,180],['pitch',-89,89],['roll',-180,180],['distance',2,500],['fov',25,120]] as const)m.camera[k]=finite(camera[k],lo,hi,'camera '+k);
 if(d.cameraMode!=='orbit'&&d.cameraMode!=='look')throw new RangeError('Camera mode');m.cameraMode=d.cameraMode;m.setVelocity(finite(d.flightSpeed,-40,40,'flight speed'));
 const wo=windowOptions(plain(d.windowOptions));if(!Array.isArray(d.windows)||d.windows.length<1||d.windows.length>12)throw new RangeError('1..12 windows required');const wm=new WindowManager();wm.viewport={width,height};wm.configure({...wo,durationMs:0});
 for(const entry of d.windows){const w=plain(entry);const id=wm.add({title:String(w.title??''),x:finite(w.x,-240,240,'window x'),y:finite(w.y,-100,100,'window y'),width:finite(w.width,30,120,'window width'),height:finite(w.height,8,60,'window height'),depth:finite(w.depth,-12,70,'depth'),shape:w.shape as typeof wo.shape}),node=wm.get(id);node.yaw=finite(w.yaw,-70,70,'yaw');node.pitch=finite(w.pitch,-65,65,'pitch');node.roll=finite(w.roll,-60,60,'roll');if(!['normal','minimized','closed'].includes(String(w.mode)))throw new RangeError('Window mode');if(typeof w.maximized!=='boolean'||typeof w.rolled!=='boolean')throw new RangeError('Window state');if(w.maximized)wm.action(id,'maximize',0);if(w.rolled)wm.toggleRoll(id,0);if(w.mode!=='normal')wm.hide(id,0,w.mode==='closed');const alpha=finite(w.alpha,0,1,'window alpha');node.fade={from:alpha,to:alpha,at:0,duration:0};}
 wm.configure(wo);const selected=finite(d.selectedWindow,1,wm.windows.length,'selected window');if(!Number.isInteger(selected))throw new RangeError('Window ID');wm.focus(selected);m.workspace=wm;m.notice='Imported v0.5 visual settings. Transcripts and input were not restored.';return m;
}
