import type {NativeCommand,SourceModalInfo} from './contracts.js';
const push:NativeCommand={op:'source-modal',action:'push',entry:{id:'same',kind:'drawer-right',title:'title',body:'body',atMs:0,dismissible:true},context:'commands'};
const edit:NativeCommand={op:'source-modal',action:'edit',query:'query',selected:4};
const association:NativeCommand={op:'source-modal',action:'associate',componentIds:[49999],boxId:49999};
// @ts-expect-error missing authored context
const missing:NativeCommand={op:'source-modal',action:'push',entry:{id:'x',kind:'center',title:'',body:'',atMs:0,dismissible:true}};
// @ts-expect-error no arbitrary modal kind
const kind:NativeCommand={op:'source-modal',action:'push',entry:{id:'x',kind:'invented',title:'',body:'',atMs:0,dismissible:true},context:''};
// @ts-expect-error explicit null is not an omitted string
const query:NativeCommand={op:'source-modal',action:'edit',query:null};
void [push,edit,association,missing,kind,query];

import {SourceModalController,composeSourceModal} from './source_modal.mjs';
import type {NativeScene} from './native_scene.mjs';
declare const scene:NativeScene;const controller=new SourceModalController(scene,{timeMs:()=>400,windows:()=>[],commands:()=>[]});controller.push('confirmation','modal');controller.edit({query:'all retained Unicode',selected:0});controller.key('Escape');
// @ts-expect-error original kind enumeration is closed
controller.push('invented','modal');
// @ts-expect-error query must be explicit source text
controller.edit({query:null});
void composeSourceModal;
