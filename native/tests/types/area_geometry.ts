import type {NativeScene} from '../../bindings/typescript/native_scene.mjs';
import type {NativeCommand} from '../../bindings/typescript/contracts.js';
function geometry(s:NativeScene){const owned:number[]|null=s.areaGeometry(1);return owned;}
const area:NativeCommand={op:'area',id:1,parent:2,x:3,y:-8,width:50,height:8,layout:'direct',padding:1,margin:2,border:'heavy',alpha:.6,material:3,hideEmpty:true,speedX:10,speedY:2,fadeMs:500,gapMs:200};
// @ts-expect-error an area geometry query requires a numeric identity
function bad(s:NativeScene){return s.areaGeometry('one');}
void [geometry,area,bad];
