import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const leaf:NativeCommand={op:'style-rule',id:1,selector:{family:'emitter',id:1},style:{surfaceAlpha:{path:'/surface',inputMin:0,inputMax:100,outputMin:.2,outputMax:1},veinContrast:{path:'/veins',inputMin:0,inputMax:100,outputMin:1,outputMax:0}}};
const mesh:NativeCommand={op:'style-rule',id:2,selector:{family:'mesh',id:0},style:{color:0x51c4d3}};
// @ts-expect-error leaf-only properties are not window appearance
const bad:NativeCommand={op:'style-rule',id:3,selector:{family:'window',id:1},style:{surfaceAlpha:.5}};
void [leaf,mesh,bad];
