/** Explicit source geometry input shared by browser and actual WASM gallery worker. */
export function decodeGalleryModel(study){
 if(!Object.hasOwn(study,'modelRecords'))return null;
 const text=study.modelRecords;if(typeof text!=='string'||/[^A-Za-z0-9+/=]/.test(text))throw Error('Model resource must be canonical base64');
 let binary;try{binary=atob(text);}catch{throw Error('Model resource must be canonical base64');}
 if(btoa(binary)!==text||binary.length%40)throw Error('Model resource must be canonical aligned base64');
 const pending=study.commands.slice();while(pending.length){const command=pending.pop();if(command.op==='reset')throw Error('Model resource recipe cannot reset its resource');if(command.op==='batch')pending.push(...command.commands);}
 return Uint8Array.from(binary,c=>c.charCodeAt(0));
}
export function verifyGalleryModel(scene,study,records){
 if(records===null)return;const actual=scene.modelRecords();if(actual.length!==records.length||actual.some((v,i)=>v!==records[i]))throw Error('Gallery model resource differs');
 const minimum=study.modelVisibleMinCells;if(minimum===undefined)return;if(!Number.isInteger(minimum)||minimum<1)throw Error('Invalid model raster minimum');
 const saved=scene.snapshot(),full=scene.render().bytes.slice();
 try{for(const sample of [new Uint8Array(),records.slice(0,256*40)]){scene.setModelRecords(sample);const other=scene.render().bytes;let changed=0;for(let i=0;i<full.length;i+=16){for(let k=0;k<12;k++)if(full[i+k]!==other[i+k]){changed++;break;}}if(changed<minimum)throw Error('Gallery full model raster missing');}}
 finally{scene.restore(saved);}
 const restored=scene.snapshot();if(restored.length!==saved.length||restored.some((v,i)=>v!==saved[i]))throw Error('Gallery model verification restore differs');
}
