import type {NativeCommand,NumericUnit} from '../../bindings/typescript/contracts.js';
const units:NumericUnit[]=['seconds','milliseconds','microseconds','nanoseconds','minutes','hours','meters','centimeters','millimeters','kilometers','degrees','radians','celsius','fahrenheit','kelvin'];
const commands:NativeCommand[]=units.map(from=>({op:'trigger',id:1,target:'/out',whenExpression:{greaterThan:[{convert:{value:{path:'/input'},from,to:from}},0]},expression:.75}));
// @ts-expect-error unit names are closed
const bad:NativeCommand={op:'trigger',id:1,target:'/out',whenExpression:{greaterThan:[{convert:{value:1,from:'unknown',to:'meters'}},0]},expression:1};
void [commands,bad];
