/** Original Studio / Observatory data sources. Rendering remains in NativeScene.
 * Studio source b4d328db… setValue/feed; Observatory source c221beb6… demoData/scope.
 * Values are synthetic demonstrations, never measurements of the host. */
function time(value){if(!Number.isSafeInteger(value)||value<0)throw RangeError('Nonnegative integer milliseconds required');return value;}
/** The original nsStageTweenWords easing=1 integer arithmetic, checked against
 * the independently executed original WASM. This computes data, not pixels. */
export function studioTween(from,to,elapsedMs,durationMs=500){
 if(!durationMs||elapsedMs>=durationMs)return to;
 let p=Math.trunc(elapsedMs*1000/durationMs);p=Math.trunc(p*p*(3000-2*p)/1000000);
 return from+Math.trunc((to-from)*p/1000);
}
export class StudioDataSource{
 constructor(){this.elapsedMs=0;this.motionMs=5000;this.nextMs=47;this.dataCount=0;this.value=670;this.fromValue=670;this.changedMs=0;this.playing=true;this.prompt='';}
 advanceTo(elapsedMs,{playing=true,onCommit}={}){time(elapsedMs);if(elapsedMs<this.elapsedMs)throw RangeError('Unordered Studio source time');if(typeof playing!=='boolean')throw TypeError('playing must be boolean');this.playing=playing;
  while(this.nextMs<=elapsedMs){this.motionMs=5000+this.nextMs;this.elapsedMs=this.nextMs;this.setValue((this.dataCount*37+431)%1001);if(onCommit)onCommit(this.snapshot());this.nextMs+=47;}
  this.elapsedMs=elapsedMs;this.motionMs=5000+elapsedMs;return this.snapshot();
 }
 setValue(value){if(!Number.isSafeInteger(value)||value<0||value>1000)throw RangeError('Studio source value0..1000');this.fromValue=studioTween(this.fromValue,this.value,Math.max(0,Math.floor(this.motionMs)-this.changedMs),this.playing?500:0);this.value=value;this.changedMs=Math.floor(this.motionMs);this.dataCount++;return this.snapshot();}
 promptCommit(text){if(typeof text!=='string')throw TypeError('Prompt text required');this.prompt=text;this.dataCount++;return this.snapshot();}
 snapshot(){return {elapsedMs:this.elapsedMs,motionMs:this.motionMs,nextMs:this.nextMs,dataCount:this.dataCount,value:this.value,fromValue:this.fromValue,changedMs:this.changedMs,displayValue:studioTween(this.fromValue,this.value,Math.max(0,this.motionMs-this.changedMs),this.playing?500:0),playing:this.playing,prompt:this.prompt};}
}
export function observatorySample(dataMs){time(dataMs);const t=dataMs/1000;
 const waveform=Array.from({length:128},(_,i)=>(Math.sin(i*.12+t*1.6)*.42+Math.sin(i*.32-t*.9)*.19)*(.75+.15*Math.sin(t)));
 const reference=waveform.map((v,i)=>Math.max(0,Math.min(1,.5+Math.sin(i*.075+dataMs*.0003)*.3)));
 const bus=[['demo.audio',.3+.24*Math.sin(t*1.8)],['demo.heat',51+7*Math.sin(t*.12)],['demo.network',18+12*Math.sin(t*.6)]].map(([source,value])=>({source,value,atMs:dataMs,quality:'synthetic'}));
 return {dataMs,waveform,reference,bus,quality:'synthetic'};
}
