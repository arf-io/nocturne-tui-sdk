import type {NativeCommand, NumericValueBinding} from '../../bindings/typescript/contracts.js';
const burst:NumericValueBinding={family:'emitter',id:1,field:'residualMs'};
const circuit:NumericValueBinding={family:'electrical-arc',id:7,field:'repeatMs'};
const command:NativeCommand={op:'define',path:'/arc/alpha',value:.5,binding:{family:'electrical-arc',id:7,field:'alpha'}};
// @ts-expect-error graph topology is immutable in numeric animation
const topology:NumericValueBinding={family:'electrical-arc',id:7,field:'points.0.x'};
// @ts-expect-error source seed is not a numeric circuit control
const seed:NumericValueBinding={family:'electrical-arc',id:7,field:'seed'};
// @ts-expect-error burst controls use numeric values
const flag:NativeCommand={op:'define',path:'/glitter',value:true,binding:{family:'emitter',id:1,field:'glitterDepth'}};
void [burst,circuit,command,topology,seed,flag];
const registration:NativeCommand={op:'state-register',id:21,path:'/alarms/circuit',role:'alarm',target:{family:'electrical-arc',id:7}};
const appearance:NativeCommand={op:'style-rule',id:1,selector:{family:'electrical-arc',role:'alarm'},style:{alpha:.2,material:2}};
// @ts-expect-error electrical circuit appearance has no surface sampling
const sampled:NativeCommand={op:'style-rule',id:2,selector:{family:'electrical-arc'},style:{sampling:'pixel'}};
void [registration,appearance,sampled];
