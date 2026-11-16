export function equalBytes(left,right){
 if(!(left instanceof Uint8Array)||!(right instanceof Uint8Array))throw TypeError('Owned byte arrays required');
 if(left.length!==right.length)return false;
 const words=Math.floor(left.length/4);let index=0;
 if(left.byteOffset%4===0&&right.byteOffset%4===0){
  const a=new Uint32Array(left.buffer,left.byteOffset,words),b=new Uint32Array(right.buffer,right.byteOffset,words);
  for(;index<words;index++)if(a[index]!==b[index])return false;
 }else{
  const a=new DataView(left.buffer,left.byteOffset,left.length),b=new DataView(right.buffer,right.byteOffset,right.length);
  for(;index<words;index++)if(a.getUint32(index*4)!==b.getUint32(index*4))return false;
 }
 for(index=words*4;index<left.length;index++)if(left[index]!==right[index])return false;
 return true;
}
export function matches(actual,expected){
 if(expected!==null&&typeof expected==='object'&&!Array.isArray(expected))return actual!==null&&typeof actual==='object'&&Object.entries(expected).every(([key,value])=>matches(actual[key],value));
 if(Array.isArray(expected))return Array.isArray(actual)&&actual.length===expected.length&&expected.every((value,index)=>matches(actual[index],value));
 return actual===expected;
}
export function projectOwnership(scene){
 const saved=scene.snapshot();
 try{scene.command({op:'remove-value',path:'/ownership/control'});return scene.snapshot();}
 finally{scene.restore(saved);}
}
export function heldAutomaticExpected(scene){
 const saved=scene.snapshot();
 try{scene.command({op:'pause',paused:true});return scene.snapshot();}
 finally{scene.restore(saved);}
}
