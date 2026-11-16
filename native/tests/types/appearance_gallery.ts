import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const map:NativeCommand={op:'style-rule',id:1,priority:10,enabled:true,selector:{family:'widget',pathPrefix:'/app',states:{selected:true}},style:{alpha:{path:'/opacity',inputMin:0,inputMax:100,outputMin:1,outputMax:0},backgroundMaterial:2,sampling:'inherit'}};
// @ts-expect-error exact path and pathPrefix cannot coexist
const bad:NativeCommand={op:'style-rule',id:2,selector:{family:'widget',path:'/app',pathPrefix:'/app'},style:{alpha:1}};
void [map,bad];
