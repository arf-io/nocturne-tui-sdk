import {NativeScene} from './native_scene.mjs';

const SCHEMA='nocturne.composition.v1';

function ownedJson(value){
 return JSON.parse(JSON.stringify(value,(_key,item)=>{
  if(typeof item==='number'&&!Number.isFinite(item))throw new TypeError('Composition numbers must be finite');
  if(['function','symbol','bigint'].includes(typeof item))throw new TypeError('Composition must contain JSON values');
  return item;
 }));
}

function validateDocument(value){
 if(value===null||typeof value!=='object'||Array.isArray(value)||
    value.schema!==SCHEMA||Object.keys(value).some(key=>!['schema','seed','commands'].includes(key)))
  throw new TypeError('Unsupported composition document');
 if(!Number.isInteger(value.seed)||value.seed<0||value.seed>0xffffffff)
  throw new TypeError('Composition seed must be uint32');
 if(!Array.isArray(value.commands)||value.commands.some(command=>
    command===null||typeof command!=='object'||Array.isArray(command)||typeof command.op!=='string'))
  throw new TypeError('Composition commands must be command objects');
 return ownedJson(value);
}

export function compositionDocument(commands,seed=2030){
 return validateDocument({schema:SCHEMA,seed,commands});
}

export function exportComposition(document){
 return JSON.stringify(validateDocument(document),null,2)+'\n';
}

export function importComposition(text){
 if(typeof text!=='string')throw new TypeError('Composition import requires JSON text');
 return validateDocument(JSON.parse(text));
}

export function applyComposition(scene,document){
 const owned=validateDocument(document);
 return owned.commands.length?scene.command({op:'batch',commands:owned.commands}):0;
}

export function assignCompositionField(command,path,value){
 const result=ownedJson(command),tokens=path.split('.').map(part=>{
  const match=/^([A-Za-z_$][\w$-]*)(\[\])?$/.exec(part);
  if(!match||['__proto__','constructor','prototype'].includes(match[1]))throw TypeError('Invalid field path');
  return {key:match[1],array:!!match[2]};
 });
 const assign=(owner,index,item)=>{
  if(owner===null||typeof owner!=='object'||Array.isArray(owner))throw TypeError('Conflicting nested parameter');
  const {key,array}=tokens[index],last=index===tokens.length-1;
  if(array){
   if(!Array.isArray(item))throw TypeError('Array field requires an array of element values');
   if(owner[key]===undefined)owner[key]=item.map(()=>({}));
   if(!Array.isArray(owner[key])||owner[key].length!==item.length)throw TypeError('Conflicting array parameter length');
   item.forEach((entry,position)=>{if(last)owner[key][position]=ownedJson(entry);else assign(owner[key][position],index+1,entry);});
  }else if(last)owner[key]=ownedJson(item);
  else {if(owner[key]===undefined)owner[key]={};assign(owner[key],index+1,item);}
 };
 assign(result,0,value);return result;
}

export async function previewComposition(wasm,document,{timeUs=0}={}){
 const owned=validateDocument(document);
 const scene=await NativeScene.create(wasm,owned.seed);
 try{
  applyComposition(scene,owned);
  if(timeUs!==0)scene.advanceTo(timeUs);
  return {document:owned,frame:scene.render(),snapshot:scene.snapshot(),info:scene.infoComplete()};
 }finally{scene.close();}
}
