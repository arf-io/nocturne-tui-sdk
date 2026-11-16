import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const node:NativeCommand={op:'node',id:1,shaPrefix:8,showKind:false,showStatus:true,showSha:true,showDetail:false};
const dwell:NativeCommand={op:'status',id:1,text:'日本',startTimeUs:250000,dwellPerCharacterMs:30,minDurationMs:100,maxDurationMs:500};
const action:NativeCommand={op:'status',id:1,text:'Review',actions:[{id:1,label:'Review',event:'/review',dismiss:false}]};
// @ts-expect-error display flags are Boolean
const bad:NativeCommand={op:'node',id:1,showSha:'yes'};
void [node,dwell,action,bad];
