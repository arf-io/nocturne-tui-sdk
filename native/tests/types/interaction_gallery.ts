import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const rule:NativeCommand={op:'character-rule',rule:{id:'selection',enabled:true,backgroundEffects:[{type:'invert',where:'unselected'}]}};
const trigger:NativeCommand={op:'trigger',id:1,target:'/out',event:'/host/approved',valueFrom:'intentValue',when:{intentValue:{comparison:'between',min:3,max:5,hysteresis:0}}};
const value:NativeCommand={op:'define',path:'/owned',value:{status:'ready'},readonly:true};
// @ts-expect-error intent predicates cannot retain numeric hysteresis
const bad:NativeCommand={op:'trigger',id:1,target:'/out',when:{intentValue:{comparison:'above',value:1,hysteresis:2}}};
void [rule,trigger,value,bad];
