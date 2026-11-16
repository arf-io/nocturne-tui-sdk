import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const boolean:NativeCommand={op:'set',path:'/out',expression:{and:[{path:'/ready'},{greaterThan:[{path:'/input'},0]}]}};
const text:NativeCommand={op:'set',path:'/title',expression:{concat:[{literal:'Count '},{path:'/label'}]}};
const object:NativeCommand={op:'set',path:'/record',expression:{object:{done:{path:'/input'},ready:{path:'/ready'}}}};
const chart:NativeCommand={op:'set',path:'/series',expression:{array:[1,2,{multiply:[2,3]}]}};
// @ts-expect-error direct constant and expression operands are exclusive
const bad:NativeCommand={op:'set',path:'/out',value:true,expression:{literal:false}};
void [boolean,text,object,chart,bad];
