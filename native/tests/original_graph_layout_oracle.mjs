import {readFileSync,writeFileSync} from 'node:fs';import {gunzipSync} from 'node:zlib';import {createHash} from 'node:crypto';import vm from 'node:vm';
const source=gunzipSync(readFileSync(new URL('./fixtures/original-rc2-workbench-docs.html.gz',import.meta.url))).toString();if(createHash('sha256').update(source).digest('hex')!=='375c4468c886728bc790b8d8cc3bdddc2a046532a4d792cde190f1b522a66385')throw Error('original source identity');
const a=source.indexOf('const {LAYOUT_MODES,DEFAULT_LAYOUT_OPTIONS'),b=source.indexOf('const {DEFAULT_CAMERA',a),u=source.indexOf('const clamp = (v, a, b)'),v=source.indexOf('const hex =',u);
const context=vm.createContext({});vm.runInContext(source.slice(u,v)+source.slice(a,b)+';globalThis.layout=layoutGraph;',context);
writeFileSync(process.argv[3],JSON.stringify(JSON.parse(readFileSync(process.argv[2])).map(r=>context.layout(r.graph,r.options))));
