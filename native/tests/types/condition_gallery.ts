import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const condition:NativeCommand={op:'trigger',id:1,target:'/out',action:'increment',value:1,edge:'level',cooldownMs:100,when:{all:[{path:'/signal',comparison:'above',value:50,hysteresis:5},{not:{path:'/enabled',comparison:'equal',value:0}}]}};
// @ts-expect-error scalar source and condition expression are exclusive
const bad:NativeCommand={op:'trigger',id:2,source:'/signal',target:'/out',whenExpression:true};
void [condition,bad];
