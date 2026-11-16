import {NativeScene} from '../bindings/typescript/native_scene.mjs';
import type {NativeCommand} from '../bindings/typescript/contracts.js';
/** Caller supplies compiled WASM bytes. This function opens no terminal or connection. */
export async function createAutumn(bytes:Uint8Array){
 const scene=await NativeScene.create(bytes,2030);
 const command:NativeCommand={op:'emitter',id:1,effect:'weather/autumn-drift',count:60,wind:[1,0,2],gravity:[0,-4,0]};
 scene.command(command);scene.advanceTo(900000);return scene.render();
}

/** Queue and explicitly acknowledge local UI intentions; never execute a provider. */
export function exerciseNotification(scene:NativeScene) {
// Notification actions are retained intentions; an application chooses how to handle them.
const notification: NativeCommand = {op:'status',id:81,text:'Inspect the completed native build',important:true,
 mode:'pop',durationMs:0,actions:[{id:1,label:'Inspect',event:'/build/inspect',value:81}]};
scene.command(notification);
scene.command({op:'notification-action',id:81,actionId:1});
for (const intention of scene.info().intents) {
  // In this example no provider or shell action is executed.
  scene.command({op:'ack-intent',id:intention.id});
}
scene.command({op:'ack-status',id:81});
scene.command({op:'dismiss',id:81});
scene.command({op:'purge-status',id:81});

}

const pearlPlot: import("../bindings/typescript/contracts.js").WidgetOptions = {id:31,kind:"donut",sampling:"braille",cellAspect:2,innerRadius:.8,startAngle:-90,sweepAngle:270,revealMs:1600,replay:true};
void pearlPlot;

/** This rule observes registered values; it never executes code from a condition. */
export const readyRule:NativeCommand={op:'trigger',id:6,target:'/demo/approved',action:'increment',value:1,
 event:'/demo/approve',when:{all:[{path:'/demo/heat',comparison:'above',value:50,hysteresis:5},
 {any:[{path:'/demo/enabled',comparison:'equal',value:1},{path:'/demo/pressure',comparison:'below',value:5}]}]}};
export const mixedPolicies:NativeCommand[]=[{op:'floor',sampling:'half'},
 {op:'emitter',id:9,effect:'weather/autumn-drift',sampling:'braille',surfaceAlpha:.12},
 {op:'emitter-style',id:9,sampling:'cell'}];
