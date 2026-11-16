import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {execFileSync} from 'node:child_process';
const temporary=mkdtempSync(join(tmpdir(),'nocturne-context-inventory-'));
try{
 const cases=join(temporary,'cases.json'),output=join(temporary,'coverage.json');
 const guard={equal:[{add:[{path:'/input'},1]},2]};
 const commands=[
  {op:'trigger',id:1,target:'/out',whenExpression:guard,value:1},
  {op:'trigger',id:2,target:'/out',whenExpression:{greaterThan:[{convert:{value:{path:'/seconds'},from:'seconds',to:'milliseconds'}},10]},value:1},
  {op:'trigger',id:3,target:'/out',when:{all:[{intentValue:{comparison:'between',min:1,max:3,hysteresis:0}},{not:{path:'/ready',comparison:'equal',value:0}}]},event:'/host/ready',value:1},
  {op:'style-rule',id:1,selector:{family:'widget',id:1},whenExpression:{equal:[{object:{answer:{multiply:[2,3]}}},{literal:{answer:6}}]},style:{alpha:.8}},
  {op:'set',path:'/out',expression:{literal:{divide:[1,0],intentField:'messageSequence',convert:{from:'kelvin',to:'celsius'}}}},
  {op:'emit-intent',event:'/host/payload',payload:{add:[1,2],intentValue:{comparison:'below',value:1}}}
 ];
 writeFileSync(cases,JSON.stringify(['isolated','application'].map(mode=>({id:'context-'+mode,mode,commands,
  actions:[{command:{op:'pause',paused:false},expectedInfo:{op:'trigger',whenExpression:{floor:1}}}]}))));
 execFileSync(process.execPath,[new URL('../scripts/gallery_option_coverage.mjs',import.meta.url).pathname,process.argv[2]||'typescript',cases,output]);
 const report=JSON.parse(readFileSync(output,'utf8'));
 const field=(op,name)=>{const row=report.fields.find(r=>r.op===op&&r.field===name);assert.ok(row,op+'.'+name);return row;};
 const add=field('trigger','whenExpression.add');
 assert.equal(add.status,'missing-demonstration','nested syntax must not become direct root syntax');
 assert.equal(add.contextStatus,'present-in-both');assert.equal(add.effectivePresenceStatus,'present-in-both');
 assert.ok(add.contextualOccurrences.some(x=>x.actualPath==='whenExpression.equal[0].add'&&x.study==='context-isolated'));
 assert.ok(add.contextualOccurrences.every(x=>x.grammar==='DataExpression'));
 const unit=field('trigger','whenExpression.convert.from');
 assert.ok(!unit.missingContextualIsolatedChoices.includes('seconds'));assert.ok(unit.missingContextualIsolatedChoices.includes('kelvin'));
 assert.equal(field('trigger','when.intentValue.comparison').contextStatus,'present-in-both');
 assert.ok(!field('trigger','when.intentValue.comparison').missingContextualApplicationChoices.includes('between'));
 assert.equal(field('style-rule','whenExpression.multiply').contextStatus,'present-in-both','dynamic object expression values are real operands');
 assert.equal(field('set','expression.divide').contextStatus,'missing-demonstration','literal JSON must remain opaque');
 assert.equal(field('set','expression.intentField').contextStatus,'missing-demonstration','literal keys are data');
 assert.equal(field('trigger','whenExpression.floor').contextStatus,'missing-demonstration','oracle metadata must not count');
 assert.equal(add.semanticAcceptance,'not-established-by-presence');
 console.log('PASS real TypeScript recursive context witnesses and literal/payload/oracle exclusions');
}finally{rmSync(temporary,{recursive:true,force:true});}
