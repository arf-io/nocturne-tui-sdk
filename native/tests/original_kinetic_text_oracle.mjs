import fs from 'node:fs';import vm from 'node:vm';import crypto from 'node:crypto';
const html=fs.readFileSync(process.argv[2],'utf8');
if(crypto.createHash('sha256').update(html).digest('hex')!=='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')throw Error('original identity');
function between(a,b){const i=html.indexOf(a),j=html.indexOf(b,i);if(i<0||j<0)throw Error(a);return html.slice(i,j);}
const helpers=between('const TAU = Math.PI * 2;','/** An explicit monotonic clock.'),paint=between('const BRAILLE_BITS =','function createCamera('),sampler=between('const TEXT_REVEALS =','return {TEXT_REVEALS,TEXT_HIDES,DEFAULT_TEXT_OPTIONS,TEXT_CONTROLS,validateTextOptions,textDuration,sampleText,TextActor};');
const data=JSON.parse(html.match(/const DATA=(\{.*?\});\s*(?:const|function)/s)[1]),wasm=Buffer.from(data.wasm,'base64');
if(crypto.createHash('sha256').update(wasm).digest('hex')!=='aa04c1705a5982b924d420971bfcbc7bbedd49f1ea527a9900531b61b0c92a09')throw Error('original palette identity');
const engine=(await WebAssembly.instantiate(wasm,{})).instance.exports;
const requests=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));const ctx=vm.createContext({requests,engine});
vm.runInContext(helpers+paint+sampler+`
result=requests.map(c=>{const poses=sampleText(c.text,c.timeMs,c.options),f={width:c.width,height:c.height,cells:Uint32Array.from(c.cells)},style=c.style;
 for(const g of poses){if(g.opacity<=0)continue;const h=((Math.round(style.hueOffset+g.index*style.hueStep+c.timeMs*style.textHueSpeed/1000+g.hue)%360)+360)%360;const color=engine.nsOklchColor(Math.round(style.textLightness*1000),Math.round(style.textChroma*10000),h*1000);putCell(f,g.x,g.y,g.glyph.codePointAt(0),color,g.opacity*style.alpha);}
 return {poses,cells:Array.from(f.cells)};});`,ctx);
process.stdout.write(JSON.stringify(ctx.result));
