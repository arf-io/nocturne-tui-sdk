import type {NativeCommand,NumericValueBinding,BooleanValueBinding} from '../../bindings/typescript/contracts.js';
const field:NativeCommand={op:'field',rings:3,continuous:true,falloff:4,frequency:200,phase:90,interference:.5,velocity:[2,-1],surface:{x:2,y:3,width:40,height:12},material:2};
const remove:NativeCommand={op:'remove-field',id:1};
const control:NumericValueBinding={family:'field',id:1,field:'interference'};
const active:BooleanValueBinding={family:'field',id:1,field:'continuous'};
// @ts-expect-error velocity contains exactly two axes
const bad:NativeCommand={op:'field',velocity:[1,2,3]};
// @ts-expect-error continuous is boolean
const badFlag:NativeCommand={op:'field',continuous:1};
// @ts-expect-error declared surface requires height
const badSurface:NativeCommand={op:'field',surface:{x:0,y:0,width:12}};
void [field,remove,control,active,bad,badFlag,badSurface];
