import {NativeScene} from '../bindings/typescript/native_scene.mjs';
import type {NativeCommand, RegisteredStateInfo, StyleRuleOptions} from '../bindings/typescript/contracts.js';

/** Register an existing button and attach a reversible, clamped alpha map.
 * Inputs: a caller-owned NativeScene. Outputs: native transactions and metadata.
 * Errors: the C contract rejects missing identities, invalid fields and capacity.
 * Example: await NativeScene.create(wasm); attachLoadAppearance(scene);
 * No renderer, provider, file or terminal is created by this function.
 */
export function attachLoadAppearance(scene:NativeScene):RegisteredStateInfo[] {
 const appearance:StyleRuleOptions={id:1,selector:{family:'widget',role:'control'},
   style:{alpha:{path:'/app/load',inputMin:0,inputMax:100,outputMin:.1,outputMax:.9}}};
 const commands:NativeCommand[]=[
   {op:'widget',id:1,kind:'button',text:'Select',x:8,y:8,width:30,height:3,material:1,alpha:.2},
   {op:'define',path:'/app/load',value:25},
   {op:'state-register',id:1,path:'/app/action',role:'control',target:{family:'widget',id:1}},
   {op:'style-rule',...appearance},
 ];
 for(const command of commands)scene.command(command);
 scene.command({op:'set',path:'/app/load',value:75});
 // This edits the authored base without replacing the active override.
 scene.command({op:'widget',id:1,alpha:.4});
 scene.command({op:'remove-style-rule',id:1});
 return scene.info().registeredStates;
}
