/** Bounded SGR mouse/keyboard demultiplexer. Never lets mouse coordinates become
 * draft text. Hosts retain keyboard decoding, terminal ownership and actions.
 */
import {StringDecoder} from 'node:string_decoder';
export class TerminalInputRouter {
 /** onKey receives non-mouse UTF-8 input; onMouse receives parsed coordinates.
  * escapeDelayMs resolves the inherently ambiguous bare Escape prefix. A partial
  * SGR report is bounded to 64 characters and discarded if malformed.
  */
 constructor(onKey,onMouse,onEscape,escapeDelayMs=60){this.onKey=onKey;this.onMouse=onMouse;this.onEscape=onEscape;this.escapeDelayMs=escapeDelayMs;this.decoder=new StringDecoder('utf8');this.pending='';this.timer=null;}
 push(bytes){clearTimeout(this.timer);this.timer=null;this.pending+=typeof bytes==='string'?bytes:this.decoder.write(bytes);this.process();if(this.pending==='\x1b')this.timer=setTimeout(()=>{this.pending='';this.onEscape();},this.escapeDelayMs);}
 process(){while(this.pending){const esc=this.pending.indexOf('\x1b');if(esc<0){this.onKey(this.pending);this.pending='';return;}if(esc>0){this.onKey(this.pending.slice(0,esc));this.pending=this.pending.slice(esc);}
  if('\x1b[<'.startsWith(this.pending))return;
  if(this.pending.startsWith('\x1b[<')){const match=/^\x1b\[<(\d{1,5});(\d{1,5});(\d{1,5})([Mm])/.exec(this.pending);if(match){this.pending=this.pending.slice(match[0].length);const button=Number(match[1]),x=Number(match[2])-1,y=Number(match[3])-1;if(x>=0&&y>=0&&x<65535&&y<65535)this.onMouse({button,x,y,down:match[4]==='M'});continue;}
   if(/^\x1b\[<[\d;]*$/.test(this.pending)&&this.pending.length<64)return;
   // Discard the malformed report, including its final character, never type it.
   const end=this.pending.slice(3).search(/[Mm]/);if(end<0){this.pending='';return;}this.pending=this.pending.slice(4+end);continue;
  }
  const next=this.pending.indexOf('\x1b',1);if(next<0){this.onKey(this.pending);this.pending='';return;}this.onKey(this.pending.slice(0,next));this.pending=this.pending.slice(next);
 }}
 /** Stop pending Escape delivery when the terminal host exits. */
 dispose(){clearTimeout(this.timer);this.timer=null;this.pending='';}
}
