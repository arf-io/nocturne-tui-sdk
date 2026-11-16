import type {NativeCommand,AppearanceExpression} from '../../bindings/typescript/contracts.js';
const guard:AppearanceExpression={equal:[{convert:{value:{path:'/input'},from:'meters',to:'centimeters'}},400]};
const trigger:NativeCommand={op:'trigger',id:1,target:'/out',whenExpression:{and:[{greaterThan:[{path:'/go'},0]},guard]},expression:{literal:.75}};
const style:NativeCommand={op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:guard,style:{alpha:.8}};
// @ts-expect-error condition and expression guards are mutually exclusive
const bad:NativeCommand={op:'style-rule',id:2,selector:{family:'widget'},whenExpression:true,when:{path:'/input',comparison:'above',value:0},style:{alpha:1}};
void [trigger,style,bad];
