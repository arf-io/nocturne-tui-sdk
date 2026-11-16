/** Window state and cell-space shape choreography. Window identity and content
 * survive minimize/close; the dock can restore either. Rendering owns no state.
 * Visibility reversal samples the present scalar, so the same geometry mapping
 * retraces continuously instead of jumping to a canned start rectangle.
 */
import {requireCellGlyph} from './cell_profile.js';
import {clamp,finite,smooth,randomAt} from './observatory.js';
export const WINDOW_EFFECTS=['fade','expand-center','expand-nw','expand-ne','expand-sw','expand-se','circle','roll-up','roll-down','drawer-left','drawer-right','drawer-top','drawer-bottom','bounce','genie','explode','accordion','origami','vortex','ribbon-unspool','petal-bloom','gravity-well'] as const;
export type WindowEffect=typeof WINDOW_EFFECTS[number];
export const WINDOW_SHAPES=['rectangle','rounded','ellipse','hexagon','diamond','capsule','ticket','cloud','polygon'] as const;
export type WindowShape=typeof WINDOW_SHAPES[number];
export type WindowAction='minimize'|'maximize'|'fade'|'close';
export interface WindowOptions {effect:WindowEffect;durationMs:number;chrome:'mac'|'windows'|'gnome'|'custom';customSide:'left'|'right';customGlyphs:string[];customOrder:WindowAction[];toolColors:Record<WindowAction,number>;toolWidth:number;toolHeight:number;shape:WindowShape;opacity:number;depth:number;yaw:number;pitch:number;roll:number;fadeFloor:number;bounce:number;scatter:number;genieBend:number;seed:number;polygon:number[][]}
export const DEFAULT_WINDOW_OPTIONS:WindowOptions={effect:'genie',durationMs:950,chrome:'mac',customSide:'right',customGlyphs:['–','□','◌','×'],customOrder:['minimize','maximize','fade','close'],toolColors:{minimize:0xe9bf65,maximize:0x7fd3ab,fade:0xbb9ae5,close:0xef8b99},toolWidth:6,toolHeight:2,shape:'rounded',opacity:.88,depth:0,yaw:0,pitch:0,roll:0,fadeFloor:.16,bounce:.18,scatter:24,genieBend:9,seed:6001,polygon:[[.05,.2],[.35,0],[.9,.12],[1,.8],[.65,1],[0,.85]]};
export const WINDOW_RANGES:Record<string,[number,number,number]>={durationMs:[0,5000,25],toolWidth:[5,10,1],toolHeight:[2,4,1],opacity:[0,1,.02],depth:[-12,70,1],yaw:[-70,70,1],pitch:[-65,65,1],roll:[-60,60,1],fadeFloor:[0,1,.02],bounce:[0,.6,.02],scatter:[0,80,1],genieBend:[-30,30,1],seed:[0,4294967295,1]};
/** Simple normalized polygon validation (3..32 vertices). Crossing edges and
 * zero area reject. Convex and concave simple masks are both supported. */
export function validatePolygon(points:number[][]):number[][]{
 if(!Array.isArray(points)||points.length<3||points.length>32)throw new RangeError('Polygon needs 3..32 vertices');const p=points.map(v=>{if(!Array.isArray(v)||v.length!==2)throw new RangeError('Polygon point');return [finite(v[0],0,1,'polygon x'),finite(v[1],0,1,'polygon y')];});
 const cross=(a:number[],b:number[],c:number[])=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);let area=0;
 for(let i=0;i<p.length;i++){const a=p[i],b=p[(i+1)%p.length];if(a[0]===b[0]&&a[1]===b[1])throw new RangeError('Duplicate polygon vertex');area+=a[0]*b[1]-b[0]*a[1];for(let j=i+1;j<p.length;j++){if(j===i+1||i===0&&j===p.length-1)continue;const c=p[j],d=p[(j+1)%p.length];if(cross(a,b,c)*cross(a,b,d)<=0&&cross(c,d,a)*cross(c,d,b)<=0&&Math.max(Math.min(a[0],b[0]),Math.min(c[0],d[0]))<=Math.min(Math.max(a[0],b[0]),Math.max(c[0],d[0]))&&Math.max(Math.min(a[1],b[1]),Math.min(c[1],d[1]))<=Math.min(Math.max(a[1],b[1]),Math.max(c[1],d[1])))throw new RangeError('Self-intersecting polygon');}}
 if(Math.abs(area)<.005)throw new RangeError('Polygon area too small');return p;
}
export function windowOptions(patch:Partial<WindowOptions>={},base:WindowOptions=DEFAULT_WINDOW_OPTIONS):WindowOptions{
 const o={...base,...patch,customGlyphs:[...(patch.customGlyphs??base.customGlyphs)],customOrder:[...(patch.customOrder??base.customOrder)],toolColors:{...(patch.toolColors??base.toolColors)},polygon:validatePolygon(patch.polygon??base.polygon)};
 for(const k of Object.keys(patch))if(!(k in DEFAULT_WINDOW_OPTIONS))throw new RangeError('Unknown window option '+k);
 for(const[k,[a,b]]of Object.entries(WINDOW_RANGES))finite(o[k as keyof WindowOptions],a,b,k);
 for(const k of ['toolWidth','toolHeight','seed'] as const)if(!Number.isInteger(o[k]))throw new RangeError(k+' integer required');
 if(!WINDOW_EFFECTS.includes(o.effect)||!WINDOW_SHAPES.includes(o.shape)||!['mac','windows','gnome','custom'].includes(o.chrome)||!['left','right'].includes(o.customSide))throw new RangeError('Window enum');
 if(o.customGlyphs.length!==4)throw new RangeError('Four single-cell custom glyphs required');o.customGlyphs.forEach(requireCellGlyph);for(const key of ['minimize','maximize','fade','close'] as const){finite(o.toolColors[key],0,0xffffff,'tool color');if(!Number.isInteger(o.toolColors[key]))throw new RangeError('Integer RGB required');}
 if(o.customOrder.length!==4||new Set(o.customOrder).size!==4||o.customOrder.some(a=>!['minimize','maximize','fade','close'].includes(a)))throw new RangeError('Custom tool order must contain all four actions');return o;
}
export function windowMask(shape:WindowShape,u:number,v:number,polygon=DEFAULT_WINDOW_OPTIONS.polygon):boolean{
 if(u<0||u>1||v<0||v>1)return false;const x=(u-.5)*2,y=(v-.5)*2;
 switch(shape){case 'rectangle':return true;case 'rounded':return Math.max(Math.abs(x)-.82,0)**2+Math.max(Math.abs(y)-.72,0)**2<=.0784;
 case 'ellipse':return x*x+y*y<=1;case 'diamond':return Math.abs(x)+Math.abs(y)<=1;
 case 'hexagon':return Math.abs(x)<=1-Math.max(0,Math.abs(y)-.45)*.45;
 case 'capsule':return (Math.max(Math.abs(x)-.62,0)/.38)**2+y*y<=1;
 case 'ticket':return Math.hypot(u,v-.5)>.105&&Math.hypot(1-u,v-.5)>.105;
 case 'cloud':return x*x/(.9*.9)+y*y/(.7*.7)<=1||(x+.48)**2+(y+.28)**2<.3||(x-.34)**2+(y+.3)**2<.38;
 case 'polygon':{let inside=false;for(let i=0,j=polygon.length-1;i<polygon.length;j=i++){const a=polygon[i],b=polygon[j];if((a[1]>v)!==(b[1]>v)&&u<(b[0]-a[0])*(v-a[1])/(b[1]-a[1])+a[0])inside=!inside;}return inside;}}
}
interface Tween {from:number;to:number;at:number;duration:number}
const tween=(t:Tween,time:number)=>t.duration===0?t.to:t.from+(t.to-t.from)*smooth((time-t.at)/t.duration);
export interface WindowSpec {title:string;x:number;y:number;width:number;height:number;shape?:WindowShape;depth?:number}
export interface ManagedWindow extends WindowSpec {id:number;shape:WindowShape;depth:number;yaw:number;pitch:number;roll:number;mode:'normal'|'minimized'|'closed';maximized:boolean;rolled:boolean;visibility:Tween;fade:Tween;maximize:Tween;body:Tween;stack:number}
export interface WindowSample {x:number;y:number;width:number;height:number;visibility:number;alpha:number;depth:number;yaw:number;pitch:number;roll:number;rolled:boolean;bodyScale:number}
export interface WindowTool {action:WindowAction;glyph:string;color:number;x:number;y:number;width:number;height:number}
/** Bounded state owner; mutation is explicit, rendering and sampling are pure.
 * All commands carry motion milliseconds. show/hide are reversible; windows
 * are never deleted by the close button, so a user can recover them in the dock.
 */
export class WindowManager {
 options=windowOptions();readonly windows:ManagedWindow[]=[];selected=0;private serial=0;private stack=0;viewport={width:136,height:44};
 configure(patch:Partial<WindowOptions>):void{this.options=windowOptions(patch,this.options);}
 add(spec:WindowSpec):number{if(this.windows.length>=12)throw new RangeError('12 window limit');if(typeof spec.title!=='string'||[...spec.title].length>80)throw new RangeError('window title');for(const [key,lo,hi]of [['x',-240,240],['y',-100,100],['width',30,120],['height',8,60]] as const)finite(spec[key],lo,hi,key);if(spec.shape&&!WINDOW_SHAPES.includes(spec.shape))throw new RangeError('window shape');finite(spec.depth??0,-12,70,'window depth');const id=++this.serial;this.windows.push({...spec,id,shape:spec.shape??this.options.shape,depth:spec.depth??0,yaw:0,pitch:0,roll:0,mode:'normal',maximized:false,rolled:false,visibility:{from:1,to:1,at:0,duration:0},fade:{from:1,to:1,at:0,duration:0},maximize:{from:0,to:0,at:0,duration:0},body:{from:1,to:1,at:0,duration:0},stack:++this.stack});this.selected=id;return id;}
 get(id:number):ManagedWindow{const w=this.windows.find(w=>w.id===id);if(!w)throw new RangeError('Unknown window');return w;}
 private set(t:Tween,to:number,time:number){finite(time,0,Number.MAX_SAFE_INTEGER,'window time');t.from=tween(t,time);t.to=to;t.at=time;t.duration=this.options.durationMs;}
 hide(id:number,time:number,closed=false):void{const w=this.get(id);this.set(w.visibility,0,time);w.mode=closed?'closed':'minimized';}
 show(id:number,time:number):void{const w=this.get(id);this.set(w.visibility,1,time);w.mode='normal';this.focus(id);}
 /** Restore visibility, ink and rolled body without discarding placement. */
 restore(id:number,time:number):void{this.show(id,time);const w=this.get(id);this.set(w.fade,1,time);this.set(w.body,1,time);w.rolled=false;}
 /** Roll the body into its tool strip, with reversible explicit-time motion. */
 toggleRoll(id:number,time:number):void{const w=this.get(id);this.set(w.body,w.rolled?1:0,time);w.rolled=!w.rolled;}
 focus(id:number):void{const w=this.get(id);this.selected=id;w.stack=++this.stack;}
 action(id:number,action:WindowAction,time:number):void{const w=this.get(id);if(action==='minimize')this.hide(id,time);else if(action==='close')this.hide(id,time,true);else if(action==='maximize'){this.set(w.maximize,w.maximized?0:1,time);w.maximized=!w.maximized;this.show(id,time);}else if(action==='fade')this.set(w.fade,w.fade.to>.5?this.options.fadeFloor:1,time);else throw new RangeError('window action');}
 sample(id:number,time:number):WindowSample{const w=this.get(id),p=tween(w.maximize,time),v=this.viewport;return {x:w.x+(3-w.x)*p,y:w.y+(6-w.y)*p,width:w.width+(v.width-6-w.width)*p,height:w.height+(v.height-15-w.height)*p,visibility:tween(w.visibility,time),alpha:tween(w.fade,time),depth:w.depth*(1-p),yaw:w.yaw*(1-p),pitch:w.pitch*(1-p),roll:w.roll*(1-p),rolled:w.rolled,bodyScale:tween(w.body,time)};}
 tasks():{id:number;title:string;mode:string;selected:boolean}[]{return this.windows.map(w=>({id:w.id,title:w.title,mode:w.mode,selected:w.id===this.selected}));}
 controls(id:number):WindowTool[]{const w=this.get(id),o=this.options;const glyphs=o.chrome==='custom'?o.customGlyphs:o.chrome==='mac'?['–','↗','◌','×']:o.chrome==='gnome'?['—','□','◐','×']:['_','□','◌','×'];const actions:WindowAction[]=o.chrome==='custom'?o.customOrder:o.chrome==='mac'?['close','minimize','maximize','fade']:['minimize','maximize','fade','close'];const side=o.chrome==='mac'?'left':o.chrome==='custom'?o.customSide:'right',start=side==='left'?1:Math.max(1,w.width-1-o.toolWidth*4);const colors=o.toolColors;return actions.map((action,i)=>({action,glyph:glyphs[['minimize','maximize','fade','close'].indexOf(action)],color:colors[action],x:start+i*o.toolWidth,y:0,width:o.toolWidth,height:o.toolHeight}));}
}
/** Map local window coordinates through a reversible visibility field. Return
 * null for unrevealed cells (circle/roll/drawer), otherwise displaced cells.
 * Position is in cell coordinates. The caller applies 3D tilt/perspective next.
 * Named experimental effects are original compositions, not a novelty claim.
 */
export function warpWindowCell(u:number,v:number,width:number,height:number,visibility:number,effect:WindowEffect,o:WindowOptions):{x:number;y:number;alpha:number}|null{
 const p=clamp(visibility,0,1),q=1-p;if(p<=0)return null;let x=u,y=v,alpha=1,cx=(width-1)/2,cy=(height-1)/2,nx=(u-cx)/Math.max(1,cx),ny=(v-cy)/Math.max(1,cy);
 if(effect==='fade')alpha=p;
 else if(effect.startsWith('expand-')){const a=effect.slice(7),ax=a.includes('w')?0:a.includes('e')?width-1:cx,ay=a.includes('n')?0:a.includes('s')?height-1:cy;x=ax+(u-ax)*p;y=ay+(v-ay)*p;alpha=Math.min(1,p*2);}
 else if(effect==='circle'){if(Math.hypot(nx,ny)>Math.SQRT2*p)return null;}
 else if(effect==='roll-up'||effect==='roll-down'){const edge=effect==='roll-up'?0:height-1;y=edge+(v-edge)*p;if(v>1&&p<.08)return null;alpha=Math.min(1,p*4);}
 else if(effect.startsWith('drawer-')){const side=effect.slice(7);if(side==='left')x=u-width*q;if(side==='right')x=u+width*q;if(side==='top')y=v-height*q;if(side==='bottom')y=v+height*q;if(x<0||x>=width||y<0||y>=height)return null;}
 else if(effect==='bounce'){const s=p+Math.sin(p*Math.PI)*o.bounce;x=cx+(u-cx)*s;y=height-1+(v-height+1)*s;alpha=Math.min(1,p*3);}
 else if(effect==='genie'){const row=v/height,s=p**(.5+row*1.4);x=cx+(u-cx)*s+Math.sin(row*Math.PI)*q*o.genieBend;y=height-1+(v-height+1)*p;alpha=Math.min(1,p*3);}
 else if(effect==='explode'){const block=Math.floor(u/3)+Math.floor(v/2)*101,r=randomAt(o.seed,block);x=u+nx*q*q*o.scatter+(r-.5)*q*6;y=v+ny*q*q*o.scatter*.5+q*q*8;alpha=p;}
 else if(effect==='accordion'){x=cx+(u-cx)*p;y=v+Math.sin(u*.5)*q*3;alpha=p;}
 else if(effect==='origami'){const fold=nx<0?-1:1;x=cx+(u-cx)*Math.cos(q*Math.PI/2);y=v+Math.abs(nx)*Math.sin(q*Math.PI)*height*.35*fold;alpha=p;}
 else if(effect==='vortex'||effect==='gravity-well'){const a=q*Math.PI*(effect==='vortex'?3:1),s=p*p,dx=u-cx,dy=(v-cy)*2;x=cx+(dx*Math.cos(a)-dy*Math.sin(a))*s;y=cy+(dx*Math.sin(a)+dy*Math.cos(a))*s/2;alpha=p;}
 else if(effect==='ribbon-unspool'){const t=clamp(p*1.6-v/height*.6,0,1);x=cx+(u-cx)*t;y=cy+(v-cy)*t+Math.sin(v*.55+q*4)*q*3;alpha=t;}
 else if(effect==='petal-bloom'){const angle=Math.atan2(ny,nx),petal=.78+.22*Math.cos(angle*6),s=clamp(p/petal,0,1);x=cx+(u-cx)*s;y=cy+(v-cy)*s;alpha=s;}
 return {x,y,alpha};
}
