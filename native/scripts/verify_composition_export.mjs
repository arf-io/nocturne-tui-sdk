#!/usr/bin/env node
import {readFileSync,readdirSync,lstatSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';
import {importComposition,previewComposition} from '../bindings/typescript/workshop_composition.mjs';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
async function main(args){
 let directory,wasmPath=fileURLToPath(new URL('../dist/nocturne_native.wasm',import.meta.url));
 for(let index=0;index<args.length;index++){
  if(args[index]==='--wasm'){wasmPath=args[++index];if(!wasmPath)throw Error('Missing WASM path');}
  else if(args[index].startsWith('--')||directory)throw Error('Unexpected argument '+args[index]);
  else directory=resolve(args[index]);
 }
 if(!directory)throw Error('Usage: node native/scripts/verify_composition_export.mjs DIRECTORY [--wasm PATH]');
 const expected=['MANIFEST.json','composition.json','scene.cells','scene.snapshot','scene-info.json'].sort();
 if(!isDeepStrictEqual(readdirSync(directory).sort(),expected))throw Error('Unexpected export file set');
 const files={};
 for(const name of expected){const path=join(directory,name);if(!lstatSync(path).isFile())throw Error('Regular export files required');files[name]=readFileSync(path);}
 const manifest=JSON.parse(files['MANIFEST.json']);
 if(manifest.schema!=='nocturne.composition-export.v1')throw Error('Unknown export schema');
 if(!isDeepStrictEqual(Object.keys(manifest.files).sort(),expected.filter(name=>name!=='MANIFEST.json')))throw Error('Invalid manifest file set');
 for(const [name,record] of Object.entries(manifest.files)){
  if(record.bytes!==files[name].length||record.sha256!==sha(files[name]))throw Error('File custody mismatch: '+name);
 }
 const wasm=readFileSync(wasmPath);if(sha(wasm)!==manifest.wasmSha256)throw Error('Requested runtime differs from export');
 const preview=await previewComposition(wasm,importComposition(files['composition.json'].toString('utf8')),{timeUs:manifest.timeUs});
 if(manifest.abiVersion!==preview.info.contract.abiVersion||manifest.snapshotSchema!=='0x'+preview.info.contract.snapshotSchema.toString(16))throw Error('ABI/schema differs from runtime');
 if(manifest.width!==preview.frame.width||manifest.height!==preview.frame.height||manifest.timeUs!==preview.info.clock.timeUs)throw Error('Frame dimensions or clock differ');
 if(sha(preview.snapshot)!==sha(files['scene.snapshot']))throw Error('Recreated snapshot differs');
 if(sha(preview.frame.bytes)!==sha(files['scene.cells']))throw Error('Recreated frame differs');
 if(!isDeepStrictEqual(preview.info,JSON.parse(files['scene-info.json'])))throw Error('Recreated metadata differs');
 return {passed:true,scope:'Independent real WASM screen export reconstruction; not full SDK qualification',
  wasmSha256:sha(wasm),documentSha256:sha(files['composition.json']),snapshotSha256:sha(preview.snapshot),frameSha256:sha(preview.frame.bytes)};
}
try{process.stdout.write(JSON.stringify(await main(process.argv.slice(2)),null,2)+'\n');}
catch(error){process.stdout.write(JSON.stringify({passed:false,error:String(error.message??error)},null,2)+'\n');process.exitCode=2;}
