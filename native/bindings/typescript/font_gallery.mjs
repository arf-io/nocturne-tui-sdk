/** Browser host presentation; native cells/source are never rewritten. */
export function createFontGallery() {
 let generation=0,serial=0,face=null;
 const base=Object.freeze({family:null,fileName:null,sha256:null,format:null,engine:'browser OpenType'});
 let current=base;
 return {
  metadata(){return {...current};},
  canvasFont(size=16){return `${size}px ${current.family?'"'+current.family+'", ':''}"DejaVu Sans Mono", "SFMono-Regular", Menlo, monospace`;},
  reset(){generation++;if(face)document.fonts.delete(face);face=null;current=base;return {...current};},
  async load(source,fileName='Local font'){
   const request=++generation;
   if(!(source instanceof ArrayBuffer)&&!ArrayBuffer.isView(source))throw TypeError('Font bytes required');
   const bytes=source instanceof ArrayBuffer?new Uint8Array(source.slice(0)):new Uint8Array(source.buffer.slice(source.byteOffset,source.byteOffset+source.byteLength));
   if(bytes.length<12)throw Error('Invalid OpenType or TrueType font');
   const magic=String.fromCharCode(...bytes.slice(0,4));
   if(magic!=='OTTO'&&magic!=='true'&&!(bytes[0]===0&&bytes[1]===1&&bytes[2]===0&&bytes[3]===0))throw Error('Expected an OpenType or TrueType sfnt font');
   const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))).map(v=>v.toString(16).padStart(2,'0')).join('');
   const family='NocturneUploadedFont_'+(++serial),candidate=new FontFace(family,bytes);
   await candidate.load();
   if(request!==generation)return {applied:false};
   document.fonts.add(candidate);const previous=face;face=candidate;
   current=Object.freeze({family,fileName:String(fileName),sha256:hash,format:magic==='OTTO'?'OpenType/CFF':'TrueType',engine:'browser OpenType',byteLength:bytes.length});
   if(previous)document.fonts.delete(previous);
   return {...current,applied:true};
  }
 };
}
/** Typography JSON ingress only; no command/script execution beyond cell-art. */
export function parseTdfCellArtImport(value){
 const commands=Array.isArray(value)?value:[value];
 if(!commands.length)throw Error('Cell-art command data required');
 const allowed=new Set(['op','id','width','height','cells','x','y','alpha','layer']);
 for(const c of commands){
  if(!c||typeof c!=='object'||Array.isArray(c)||c.op!=='cell-art'||Object.keys(c).some(k=>!allowed.has(k)))throw Error('Typography import accepts cell-art commands only');
  if(!Number.isInteger(c.id)||!Number.isInteger(c.width)||!Number.isInteger(c.height)||!Array.isArray(c.cells))throw Error('Complete cell-art data required');
 }
 return {op:'batch',commands};
}
