import assert from 'node:assert/strict';import {TerminalInputRouter} from '../../examples/fleet_input.mjs';
const keys=[],mouse=[];let escapes=0;const r=new TerminalInputRouter(v=>keys.push(v),v=>mouse.push(v),()=>escapes++,10);
r.push('hello');assert.equal(keys.join(''),'hello');
r.push('\x1b[<0;21');r.push(';5M\x1b[<0;21;5m');assert.equal(keys.join(''),'hello');assert.deepEqual(mouse[0],{button:0,x:20,y:4,down:true});assert.equal(mouse[1].down,false);
r.push('\x1b[A');assert.equal(keys.at(-1),'\x1b[A');
r.push(Buffer.from([0xc3]));r.push(Buffer.from([0xa9]));assert.equal(keys.at(-1),'é');
r.push('\x1b');await new Promise(resolve=>setTimeout(resolve,20));assert.equal(escapes,1);
r.push('\x1b[<0;badM');assert.ok(!keys.join('').includes('bad'));assert.ok(!keys.join('').includes('adM')); // malformed fields are not interpreted as a mouse click
r.dispose();console.log(JSON.stringify({suite:'terminal input demultiplexing',status:'PASS',checks:7}));
