import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const local:NativeCommand={op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:{equal:[{object:{x:{add:[1,2]}}},{literal:{x:3}}]},style:{alpha:.8}};
const data:NativeCommand={op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:{equal:[{literal:{intentField:'id',intentPath:'/ready'}},{literal:{intentField:'id',intentPath:'/ready'}}]},style:{alpha:.8}};
const event:NativeCommand={op:'trigger',id:1,target:'/out',event:'/host/ready',whenExpression:{intentPath:'/ready'},expression:{intentField:'value'}};
const condition:NativeCommand={op:'style-rule',id:1,selector:{family:'widget',id:1},when:{not:{path:'/level',comparison:'above',value:0}},style:{alpha:.8}};
// @ts-expect-error numeric intent conditions also require an event subscription
const eventCondition:NativeCommand={op:'style-rule',id:1,selector:{family:'widget',id:1},when:{not:{intentValue:{comparison:'above',value:0}}},style:{alpha:.8}};
// @ts-expect-error appearance has no event subscription
const bad:NativeCommand={op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:{equal:[{intentField:'value'},1]},style:{alpha:.8}};
// @ts-expect-error event references cannot hide in an unselected branch
const nested:NativeCommand={op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:{if:{condition:false,then:{intentPath:'/ready'},else:true}},style:{alpha:.8}};
// @ts-expect-error object expression operands retain the same ownership contract
const object:NativeCommand={op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:{equal:[{object:{x:{intentField:'id'}}},{literal:{x:1}}]},style:{alpha:.8}};
void [local,data,event,condition,eventCondition,bad,nested,object];
