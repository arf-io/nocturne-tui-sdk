import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
const temporary=mkdtempSync(join(tmpdir(),'nocturne-option-inventory-'));
try{
 const cases=join(temporary,'cases.json'),output=join(temporary,'coverage.json');
 writeFileSync(cases,JSON.stringify(['isolated','application'].map(mode=>({id:mode,mode,
  commands:[{op:'widget',id:1,kind:'donut',sampling:'braille',innerRadius:.55}],
  actions:[{command:{op:'pause',paused:false},hostSteps:[
   {command:{op:'schedule',id:31,atUs:1000000,command:{op:'batch',commands:[{op:'forces',id:1,drag:11}]}},
    hostSteps:[{command:{op:'accessibility',reducedMotion:mode==='isolated'}},{command:{op:'emitter',id:1,effect:'weather/autumn-drift',count:0}}]}],
   expectedInfo:{unused:{op:'cancel',id:65535,tailMs:123}}}]}))));
 execFileSync(process.execPath,[new URL('../scripts/gallery_option_coverage.mjs',import.meta.url).pathname,process.argv[2]||'typescript',cases,output]);
 const report=JSON.parse(readFileSync(output,'utf8'));
 const field=(op,name)=>{const row=report.fields.find(r=>r.op===op&&r.field===name);assert.ok(row,`Missing ${op}.${name}`);return row;};
 const kinds=field('widget','kind');assert.equal(kinds.choices.length,18);assert.equal(kinds.status,'present-in-both');assert.ok(!kinds.missingChoices.includes('donut'));
 assert.equal(field('widget','innerRadius').status,'present-in-both');
 assert.ok(field('window','border').choices.includes('heavy'));
 assert.ok(field('ribbon','interpolation').choices.includes('catmull-rom'));
 assert.ok(field('model-import','transform.position'));
 assert.ok(field('set','expression.intentField').choices.includes('messageSequence'));
 assert.ok(report.recursiveReferences.some(r=>r.op==='set'&&r.type==='NumericExpression'));
 assert.ok(report.recursiveReferences.some(r=>r.type.includes('SceneEdit')),'nested commands retain explicit contract references');
 assert.ok(report.fields.length<5000,'Recursive formula grammar must not be exponentially unrolled');
 const motion=field('accessibility','reducedMotion');
 assert.ok(motion.missingIsolatedChoices.includes(false));assert.ok(!motion.missingIsolatedChoices.includes(true));
 assert.ok(!motion.missingApplicationChoices.includes(false));
 const flutter=field('forces','drag');
 assert.ok(flutter.isolatedCases.includes('isolated'));assert.ok(flutter.applicationCases.includes('application'));
 const forceOp=report.operationCoverage.find(row=>row.op==='forces');assert.ok(forceOp);
 assert.ok(forceOp.isolatedCases.includes('isolated'));assert.ok(forceOp.applicationCases.includes('application'));
 assert.equal(forceOp.semanticAcceptance,'not-established-by-presence');
 assert.ok(!field('cancel','tailMs').isolatedCases.includes('isolated'),'oracle fields must not count as authoring');
 assert.ok(!field('cancel','tailMs').applicationCases.includes('application'),'oracle fields must not count as authoring');
 console.log('Authoring inventory includes intersection members and nested public options');
}finally{rmSync(temporary,{recursive:true,force:true});}
