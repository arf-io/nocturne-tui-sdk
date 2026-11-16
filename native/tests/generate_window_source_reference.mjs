// Offline original-source fixtures; no candidate native execution.
import {readFileSync,writeFileSync} from 'node:fs';
import {createRequire} from 'node:module';
import {createHash} from 'node:crypto';
import {windowVertex} from '../../bindings/continuity/kinetic-windows.js';
import {clamp,finite,smooth,randomAt} from '../../bindings/continuity/observatory.js';
const require=createRequire(import.meta.url),ts=require(process.env.NOCTURNE_TYPESCRIPT_MODULE||'typescript');
const path='legacy/atelier-v0.5/bindings/typescript/window_fx.ts',source=readFileSync(new URL('../../'+path,import.meta.url),'utf8');
const code=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ES2022}}).outputText.replace(/import[^;]+;/g,'').replace(/export /g,'');
const warp=Function('clamp','finite','smooth','randomAt','requireCellGlyph',code+';return warpWindowCell;')(clamp,finite,smooth,randomAt,x=>x);
const ledger=JSON.parse(readFileSync(new URL('../port-ledger.json',import.meta.url)));
const rows=[],uvs=[[0,0],[.2,.3],[.5,.5],[.83,.71],[1,1]],phases=[0,.04,.08,.23,.5,.91,1];
for(const entry of ledger.entries.filter(e=>e.nativeContract==='WindowTransition'))for(const seed of [42,4294967295]){
 const family=entry.oldId.split('/')[1],effect=entry.oldId.split('/')[2],W=30,H=20;
 const controls={width:W,height:H,seed,overshoot:.24,scatter:27,bend:11,folds:7,anchorX:.2,anchorY:1.3};
 const samples=[];for(const p of phases)for(const [u,v] of uvs){let expected;
  if(family==='kinetic'){
   const q=windowVertex({effect,width:W,height:H,visibility:p,yaw:0,pitch:0,roll:0,x:0,y:0,z:0,opacity:1},u,v,{seed,overshoot:controls.overshoot,explosionDistance:controls.scatter,folds:controls.folds,anchorX:controls.anchorX,anchorY:controls.anchorY});expected=[q.x,q.y,q.z,q.opacity];
  }else{
   const q=warp(u*(W-1),v*(H-1),W,H,p,effect,{seed,bounce:controls.overshoot,scatter:controls.scatter,genieBend:controls.bend});
   expected=q?[(q.x-(W-1)/2)*W/(W-1),((H-1)/2-q.y)*H/(H-1),0,q.alpha]:[(u-.5)*W,(.5-v)*H,0,0];
  }samples.push({u,v,p,expected});
 }rows.push({id:entry.newId,oldId:entry.oldId,family,controls,samples});
}
const sources={};for(const p of [path,'bindings/continuity/kinetic-windows.js','bindings/continuity/observatory.js'])sources[p]=createHash('sha256').update(readFileSync(new URL('../../'+p,import.meta.url))).digest('hex');
writeFileSync(new URL('./fixtures/window-source-reference.json',import.meta.url),JSON.stringify({origin:'Preserved original source operators and documented adapter; not native candidate',sources,rows})+'\n');
