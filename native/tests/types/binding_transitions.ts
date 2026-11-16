import type {NativeCommand} from '../../bindings/typescript/contracts.js';
const commands:NativeCommand[]=[
 {op:'bind',path:'/control',binding:null},
 {op:'bind',path:'/control',binding:{family:'camera',field:'position.x'}},
 {op:'bind',path:'/control',binding:{family:'widget',id:1,field:'value'}},
 {op:'bind',path:'/control',binding:{family:'window',id:1,field:'padding'}},
 {op:'bind',path:'/control',binding:{family:'area',id:1,field:'hideEmpty'}}];
// @ts-expect-error binding fields are closed
const bad:NativeCommand={op:'bind',path:'/control',binding:{family:'camera',field:'unsupported'}};
void [commands,bad];
