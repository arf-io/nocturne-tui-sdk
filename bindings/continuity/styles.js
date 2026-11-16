import {rgbToOklch,rgb,hex,clamp} from './observatory.js';
/** Host-neutral style tracks. Time is supplied; updating a value never waits for
 * an animation tick. Stage time is an arrival deadline measured since update. */
export const STYLE_EASINGS=['linear','smooth','ease-in','ease-out','ease-in-out','step'];
export function styleEase(t,easing='smooth') {t=clamp(t,0,1);if(easing==='step')return t===1?1:0;if(easing==='ease-in')return t*t;if(easing==='ease-out')return 1-(1-t)*(1-t);if(easing==='ease-in-out')return t<.5?2*t*t:1-2*(1-t)*(1-t);return easing==='linear'?t:t*t*(3-2*t);}
export const DEFAULT_CHANGE_STYLE=Object.freeze({easing:'smooth',gradientSpeed:0.2,gradientSpan:16,hueStep:0,
 stages:[{atMs:0,colors:['#fa645b']},{atMs:10000,colors:['#ed9a50']},{atMs:20000,colors:['#d3c466']},{atMs:30000,colors:['#8abd8b']},{atMs:60000,colors:['#89939c']}]});
export function validateChangeStyle(value={}){
 const s=JSON.parse(JSON.stringify({...DEFAULT_CHANGE_STYLE,...value}));
 for(const k of Object.keys(s))if(!['easing','gradientSpeed','gradientSpan','hueStep','stages'].includes(k))throw RangeError('Unknown color-track field '+k);
 if(!STYLE_EASINGS.includes(s.easing)||!Array.isArray(s.stages)||s.stages.length<1||s.stages.length>32)throw RangeError('Color track stages/easing');
 let previous=-1;
 for(const p of s.stages){if(!Number.isSafeInteger(p.atMs)||p.atMs<0||p.atMs>86400000||p.atMs<=previous||!Array.isArray(p.colors)||!p.colors.length||p.colors.length>32)throw RangeError('Increasing stage times and bounded colors required');previous=p.atMs;p.colors.forEach(c=>{if(typeof c!=='string'||!/^#[\da-f]{6}$/i.test(c))throw RangeError('Stage RGB hex');});if(p.easing!==undefined&&!STYLE_EASINGS.includes(p.easing))throw RangeError('Stage easing');}
 if(s.stages[0].atMs!==0)throw RangeError('First stage must be immediate (atMs=0)');
 for(const [k,lo,hi]of [['gradientSpeed',-10,10],['gradientSpan',1,1024],['hueStep',-360,360]])if(typeof s[k]!=='number'||!Number.isFinite(s[k])||s[k]<lo||s[k]>hi)throw RangeError(k);
 return s;
}
/** Stage sampling returns endpoints, fraction and currently resolved palette.
 * Exact boundaries return exact stage RGB. Intermediate colors use OKLCh when
 * engine is provided; the palette descriptor itself is also useful to native hosts. */
export function sampleChange(style,ageMs,engine){
 const t=Math.max(0,ageMs);let a=style.stages[0],b=a;
 for(let i=1;i<style.stages.length;i++){b=style.stages[i];if(t<=b.atMs)break;a=b;}
 if(t>=style.stages.at(-1).atMs)a=b=style.stages.at(-1);
 const fraction=a===b?0:styleEase((t-a.atMs)/(b.atMs-a.atMs),b.easing??style.easing);
 const colors=Array.from({length:Math.max(a.colors.length,b.colors.length)},(_,i)=>{
  const c=a.colors[i%a.colors.length],d=b.colors[i%b.colors.length];return fraction<=0?c:fraction>=1?d:engine?hex(blendOklch(engine,rgb(c),rgb(d),fraction)):c;
 });
 return {colors,from:a.colors,to:b.colors,fraction,ageMs:t,gradientSpeed:style.gradientSpeed,gradientSpan:style.gradientSpan,hueStep:style.hueStep};
}
/** Per-property update envelope. Only changed values reset the schedule. */
export class ChangeTrack {
 constructor(style={}){this.style=validateChangeStyle(style);this.value=null;this.updatedAt=0;this.revision=0;}
 configure(patch){this.style=validateChangeStyle({...this.style,...patch});}
 update(value,atMs){if(!Number.isSafeInteger(atMs)||atMs<0)throw RangeError('Explicit update time');if(typeof value!=='number'&&typeof value!=='string')throw TypeError('String or finite number');if(typeof value==='number'&&!Number.isFinite(value))throw RangeError('Finite value');if(value!==this.value){this.value=value;this.updatedAt=atMs;this.revision++;}}
 sample(atMs,engine){if(!Number.isSafeInteger(atMs)||atMs<0)throw RangeError('Explicit sample time');return sampleChange(this.style,Math.max(0,atMs-this.updatedAt),engine);}
}
/** Shortest-arc hue interpolation and fixed-lightness gamut reduction supplied by
 * the existing native converter. Achromatic endpoints borrow the other's hue. */
export function blendOklch(engine,a,b,t){if(t<=0)return a;if(t>=1)return b;let [la,ca,ha]=rgbToOklch(a),[lb,cb,hb]=rgbToOklch(b);if(ca<1e-5)ha=hb;if(cb<1e-5)hb=ha;const dh=((hb-ha+540)%360)-180;return engine.oklch(Math.round((la+(lb-la)*t)*1000),Math.round((ca+(cb-ca)*t)*10000),Math.round((ha+dh*t)*1000));}
export function gradientInk(engine,colors,index,timeMs,{gradientSpan=16,gradientSpeed=.2,hueStep=0}={}){
 const u=((index/gradientSpan+timeMs/1000*gradientSpeed)%colors.length+colors.length)%colors.length,i=Math.floor(u);let color=blendOklch(engine,rgb(colors[i]),rgb(colors[(i+1)%colors.length]),u-i);
 if(hueStep){const [l,c,h]=rgbToOklch(color);color=engine.oklch(Math.round(l*1000),Math.round(c*10000),Math.round((h+index*hueStep)*1000));}return color;
}
export const BORDER_GLYPHS={none:[' ',' ',' ',' ',' ',' '],rounded:['╭','╮','╰','╯','─','│'],square:['┌','┐','└','┘','─','│'],double:['╔','╗','╚','╝','═','║'],heavy:['┏','┓','┗','┛','━','┃']};
export const DEFAULT_DECORATION=Object.freeze({border:'rounded',background:'#10161e',alpha:.35,foreground:'#dedbd2',accent:'#8ccfc4',
 activeColor:'#8ccfc4',inactiveColor:'#7d8995',selectedColor:'#d3b0da',disabledColor:'#596575',selectedBackground:'#263a48',
 padding:1,margin:1,hueStep:17,hueSpeed:20,periodMs:1000,animate:'selected',state:'active'});
export function validateDecoration(value={}){const o={...DEFAULT_DECORATION,...value};for(const [k,v]of Object.entries(o)){if(!(k in DEFAULT_DECORATION))throw RangeError('Unknown decoration '+k);if(k==='border'&&!BORDER_GLYPHS[v])throw RangeError('Border');if(/Color$/.test(k)||['background','foreground','accent','selectedBackground'].includes(k)){if(!/^#[\da-f]{6}$/i.test(v))throw RangeError('Color '+k);}}if(!['active','selected','inactive','disabled'].includes(o.state)||!['none','active','selected','both'].includes(o.animate))throw RangeError('State animation');for(const [k,a,b]of [['alpha',0,1],['padding',0,8],['margin',0,8],['hueStep',-360,360],['hueSpeed',-360,360],['periodMs',1,120000]])if(typeof o[k]!=='number'||!Number.isFinite(o[k])||o[k]<a||o[k]>b||(['padding','margin','periodMs'].includes(k)&&!Number.isInteger(o[k])))throw RangeError(k);return o;}
export function decoratedInk(engine,style,index,timeMs){const base=rgb(style[style.state+'Color']??style.foreground),moving=style.animate==='both'?['active','selected'].includes(style.state):style.state===style.animate;if(!moving)return base;const [l,c,h]=rgbToOklch(base);return engine.oklch(Math.round(l*1000),Math.round(c*10000),Math.round((h+index*style.hueStep+timeMs/style.periodMs*style.hueSpeed)*1000));}
/** Apply a reusable decoration to native nodes without mutating them. Color
 * sweeps are sampled in OKLCh here, not the legacy kernel's HSV animator.
 * Text nodes are expanded into individually colored scalar cells when moving.
 * Insets are explicit; app layout still owns a node's outer rectangle. */
export function decorateNodes(engine,nodes,style,timeMs){
 const s=validateDecoration(style),boxStyles={rounded:0,square:1,double:2,heavy:3,none:0},states={active:1,selected:2,inactive:0,disabled:4};
 const result=[];
 for(const source of nodes){
  const n={...source,x:(source.x??0)+s.margin,y:(source.y??0)+s.margin,width:Math.max(1,(source.width??1)-2*s.margin),height:Math.max(1,(source.height??1)-2*s.margin),fg:decoratedInk(engine,s,0,timeMs),bg:rgb(s.state==='selected'?s.selectedBackground:s.background),bgOpacity:Math.round(s.alpha*1000),state:states[s.state],colorAnimation:0};
  if(n.kind==='box'||n.kind===1)n.style=boxStyles[s.border];
  if(s.border==='none'&&(n.kind==='box'||n.kind===1))continue;
  const hasText=typeof n.text==='string'&&n.text.length>0;
  if(hasText&&(n.kind==='text'||n.kind===0)){
   const width=Math.max(1,(n.width??80)-2*s.padding);let x=0,y=0;
   for(const [index,ch]of [...n.text].entries()){
    if(ch==='\n'){x=0;y++;continue;}if(x>=width){x=0;y++;}if(y>=Math.max(1,(n.height??1)-2*s.padding))break;
    result.push({...n,x:n.x+s.padding+x,y:n.y+s.padding+y,width:1,height:1,text:ch,fg:decoratedInk(engine,s,index,timeMs)});x++;
   }
  }else result.push(n);
 }
 return result;
}
/** Owned-cell style composition usable on borders, menu rows, text and values.
 * Existing native background compositing is retained; recoloring affects ink only.
 * colorAnimation=0 prevents mixing the new OKLCh sweep with the old HSV mode. */
export function paintStyled(engine,frame,nodes,style,timeMs){
 const s=validateDecoration(style),prepared=decorateNodes(engine,nodes,s,timeMs),out=engine.paint(frame,timeMs,prepared);
 for(const n of nodes){const x0=Math.max(0,Math.floor(n.x??0)),y0=Math.max(0,Math.floor(n.y??0)),x1=Math.min(out.width,x0+(n.width??1)),y1=Math.min(out.height,y0+(n.height??1));
  for(let y=y0;y<y1;y++)for(let x=x0;x<x1;x++){const k=(y*out.width+x)*4,g=out.cells[k];if((!n.id||out.cells[k+3]===n.id)&&g>32&&![0x2580,0x2584,0x258c,0x2590].includes(g))out.cells[k+1]=decoratedInk(engine,s,(y-y0)*(x1-x0)+x-x0,timeMs);}
 }
 return out;
}
