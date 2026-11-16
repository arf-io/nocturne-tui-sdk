import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const palette:NativeCommand={op:'material',id:3,space:'hsl',channels:{h:{initial:30,rate:60,min:0,max:360,periodMs:1000,boundary:'clamp',easing:'linear',seed:73},s:.8,l:.5},scope:'characters',hueStep:25,alpha:.8};
const gradient:NativeCommand={op:'material',id:3,space:'rgb',gradient:[[1,0,0],[0,1,0]],spacing:.1,index:{initial:0,rate:.2,min:0,max:1}};
// @ts-expect-error material scope is closed
const bad:NativeCommand={op:'material',scope:'unsupported'};
void [palette,gradient,bad];
