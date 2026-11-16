import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const alpha:NativeCommand={op:'material',id:3,scope:'characters',alpha:{initial:.2,step:.2,min:0,max:1}};
const clock:NativeCommand={op:'time',timeUs:500000,budget:12};
// @ts-expect-error budget is numeric
const bad:NativeCommand={op:'time',timeUs:0,budget:'unbounded'};
void [alpha,clock,bad];
