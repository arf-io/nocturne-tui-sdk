#!/usr/bin/env node
import {readFileSync,existsSync,mkdtempSync,writeFileSync,renameSync,rmSync} from 'node:fs';
import {resolve,dirname,join} from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {importComposition,previewComposition} from '../bindings/typescript/workshop_composition.mjs';

const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');

async function main(args){
 let input,output,wasmPath=fileURLToPath(new URL('../dist/nocturne_native.wasm',import.meta.url)),timeUs=0;
 for(let index=0;index<args.length;index++){
  const argument=args[index];
  if(argument==='--wasm'||argument==='--time-us'||argument==='--output'){
   const value=args[++index];
   if(value===undefined)throw Error('Missing value for '+argument);
   if(argument==='--wasm')wasmPath=value;
   else if(argument==='--output')output=resolve(value);
   else{timeUs=Number(value);if(!Number.isSafeInteger(timeUs)||timeUs<0)throw Error('Preview time must be nonnegative integer microseconds');}
  }else if(argument.startsWith('--')||input!==undefined)throw Error('Unexpected argument '+argument);
  else input=argument;
 }
 if(input===undefined)throw Error('Usage: node native/scripts/validate_composition.mjs DOCUMENT [--wasm PATH] [--time-us MICROSECONDS] [--output NEW_DIRECTORY]');
 if(output&&existsSync(output))throw Error('Export output already exists');
 const bytes=readFileSync(input),document=importComposition(bytes.toString('utf8')),wasm=readFileSync(wasmPath);
 const preview=await previewComposition(wasm,document,{timeUs});
 const result={passed:true,scope:'Independent native WASM composition preview; not full SDK qualification',
         documentSha256:sha256(bytes),wasmSha256:sha256(wasm),abiVersion:preview.info.contract.abiVersion,
         snapshotSchema:'0x'+preview.info.contract.snapshotSchema.toString(16),requestedTimeUs:timeUs,timeUs:preview.info.clock.timeUs,
         width:preview.frame.width,height:preview.frame.height,frameBytes:preview.frame.bytes.length,
         snapshotBytes:preview.snapshot.length,snapshotSha256:sha256(preview.snapshot),frameSha256:sha256(preview.frame.bytes)};
 if(output){
  const stage=mkdtempSync(join(dirname(output),'.nocturne-composition-'));
  try{
   const files={'composition.json':bytes,'scene.cells':preview.frame.bytes,'scene.snapshot':preview.snapshot,
                'scene-info.json':Buffer.from(JSON.stringify(preview.info,null,2)+'\n')};
   const manifest={schema:'nocturne.composition-export.v1',scope:result.scope,wasmSha256:result.wasmSha256,
                   abiVersion:result.abiVersion,snapshotSchema:result.snapshotSchema,timeUs:result.timeUs,
                   width:result.width,height:result.height,files:{}};
   for(const [name,data] of Object.entries(files)){
    writeFileSync(join(stage,name),data,{flag:'wx'});manifest.files[name]={bytes:data.length,sha256:sha256(data)};
   }
   writeFileSync(join(stage,'MANIFEST.json'),JSON.stringify(manifest,null,2)+'\n',{flag:'wx'});
   if(existsSync(output))throw Error('Export output appeared during validation');
   renameSync(stage,output);result.exportDirectory=output;
  }finally{rmSync(stage,{recursive:true,force:true});}
 }
 return result;
}

try{process.stdout.write(JSON.stringify(await main(process.argv.slice(2)),null,2)+'\n');}
catch(error){process.stdout.write(JSON.stringify({passed:false,error:String(error.message??error)},null,2)+'\n');process.exitCode=2;}
