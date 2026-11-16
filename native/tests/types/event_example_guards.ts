import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const commands:NativeCommand[]=[{op:'trigger',id:1,target:'/flux',event:'/host/flow',whenExpression:true,expression:{intentPath:'/flux'}},{op:'trigger',id:2,target:'/entry',event:'/host/entry',whenExpression:true,expression:{intentPath:'/value'}}];
void commands;
