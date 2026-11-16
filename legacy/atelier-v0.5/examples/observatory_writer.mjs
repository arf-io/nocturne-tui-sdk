/** Bounded terminal presentation. Input/data mutations are never throttled.
 * Frames superseded BEFORE writing may coalesce when stdout applies pressure.
 * No terminal mode ownership is hidden in this class. */
export class CellWriter {
 constructor(stream){this.stream=stream;this.previous=null;this.pending=null;this.blocked=false;this.coalesced=0;this.bytes=0;this.onDrain=()=>{this.blocked=false;if(this.pending){const f=this.pending;this.pending=null;this.present(f);}};stream.on('drain',this.onDrain);}
 encode(frame){const old=this.previous,size=!old||old.width!==frame.width||old.height!==frame.height;let out=size?'\x1b[2J':'',fg=-1,bg=-1;
  for(let y=0;y<frame.height;y++){let positioned=false;for(let x=0;x<frame.width;x++){const i=(y*frame.width+x)*4;if(!size&&frame.cells[i]===old.cells[i]&&frame.cells[i+1]===old.cells[i+1]&&frame.cells[i+2]===old.cells[i+2]){positioned=false;continue;}if(!positioned){out+=`\x1b[${y+1};${x+1}H`;positioned=true;}const f=frame.cells[i+1],b=frame.cells[i+2];if(f!==fg){out+=`\x1b[38;2;${f>>>16};${f>>>8&255};${f&255}m`;fg=f;}if(b!==bg){out+=`\x1b[48;2;${b>>>16};${b>>>8&255};${b&255}m`;bg=b;}const g=frame.cells[i];out+=g>=32&&g!==127?String.fromCodePoint(g):' ';}}
  this.previous=frame;return out+'\x1b[0m';
 }
 present(frame){if(this.blocked){if(this.pending)this.coalesced++;this.pending=frame;return;}const text=this.encode(frame);this.bytes+=Buffer.byteLength(text);this.blocked=!this.stream.write(text);}
 dispose(){this.stream.off('drain',this.onDrain);this.pending=null;}
}
