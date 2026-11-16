// Inventory the exported authoring contract with the real TypeScript compiler.
// Presence is a coverage lead, not semantic acceptance or proof of every option.
import {createRequire} from 'node:module';
import {readFileSync,writeFileSync,readdirSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const require=createRequire(import.meta.url);
const ts=require(process.argv[2]||'typescript');
const root=fileURLToPath(new URL('../',import.meta.url));
const file=path.join(root,'bindings/typescript/contracts.ts');
const program=ts.createProgram([file],{target:ts.ScriptTarget.ES2022,strict:true,noEmit:true});
const checker=program.getTypeChecker(),source=program.getSourceFile(file);
const declaration=source.statements.find(n=>ts.isTypeAliasDeclaration(n)&&n.name.text==='NativeCommand');
const commandType=checker.getTypeAtLocation(declaration);
const recursiveGrammars=source.statements.filter(n=>ts.isTypeAliasDeclaration(n)&&
 ['NumericExpression','DataExpression','AppearanceExpression','AppearanceNumericExpression','AppearanceCondition','ValueCondition','EventPayload'].includes(n.name.text))
 .map(n=>checker.getTypeAtLocation(n));
const grammarCache=new Map(),equivalenceCache=new Map();
function equivalent(a,b){
 if(a.id===b.id)return true;
 const key=a.id+':'+b.id;
 if(!equivalenceCache.has(key))equivalenceCache.set(key,checker.isTypeAssignableTo(a,b)&&checker.isTypeAssignableTo(b,a));
 return equivalenceCache.get(key);
}
function grammarOf(type){
 if(grammarCache.has(type.id))return grammarCache.get(type.id);
 const members=type.isUnion()?type.types:[type];
 // Mapped recursive types can instantiate equivalent members with different IDs.
 // Mutual compiler assignability recognizes their canonical grammar ancestry.
 const result=recursiveGrammars.filter(g=>(g.isUnion()?g.types:[g]).every(t=>members.some(m=>equivalent(t,m))))
  .sort((a,b)=>(b.isUnion()?b.types.length:1)-(a.isUnion()?a.types.length:1))[0];
 grammarCache.set(type.id,result);return result;
}
function substantive(type){
 return !(type.isUnion()?type.types:[type]).every(t=>t.flags&(ts.TypeFlags.Never|ts.TypeFlags.Undefined));
}
const cases=JSON.parse(readFileSync(process.argv[3],'utf8'));
const usage=new Map();
function record(command,study,commandLocation){
 if(!command||typeof command!=='object'||!command.op)return;
 const rows=usage.get(command.op)||[];rows.push({study:study.id,mode:study.mode,command,commandLocation});usage.set(command.op,rows);
 if(command.op==='schedule')record(command.command,study,commandLocation+'.command');
 if(command.op==='batch')command.commands.forEach((child,i)=>record(child,study,commandLocation+'.commands['+i+']'));
}
const applicationRecipes=JSON.parse(readFileSync(path.join(root,'recipes.json'),'utf8'));
for(const [i,recipe] of applicationRecipes.entries())recipe.commands.forEach((command,k)=>record(command,{id:recipe.id,mode:'application'},'recipes['+i+'].commands['+k+']'));
function recordAction(action,study,location){
 (action.hostSteps||[]).forEach((step,i)=>recordAction(step,study,location+'.hostSteps['+i+']'));
 record(action.command,study,location+'.command');
}
for(const [i,study] of cases.entries()){study.commands.forEach((command,k)=>record(command,study,'cases['+i+'].commands['+k+']'));(study.actions||[]).forEach((action,k)=>recordAction(action,study,'cases['+i+'].actions['+k+']'));}
const descriptors=new Map(),recursiveReferences=new Map(),truncatedReferences=new Map(),contextRoots=new Map();
function describe(type,op,prefix='',depth=0,ancestors=new Set()){
 const reference={op,field:prefix,type:checker.typeToString(type)};
 const grammar=grammarOf(type),grammarName=grammar?.aliasSymbol?.getName();
 if(prefix&&grammarName&&grammarName!=='EventPayload'&&![...contextRoots.values()].some(r=>r.op===op&&(prefix===r.field||prefix.startsWith(r.field+'.')||prefix.startsWith(r.field+'['))))
  contextRoots.set(op+':'+prefix,{op,field:prefix,grammar:grammarName,type:grammar});
 // Nested commands reference the separately inventoried root contract.
 // Expanding all operations inside batch/schedule creates duplicate pseudo-options.
 if(prefix&&(type.id===commandType.id||type.aliasSymbol?.getName()==='SceneEdit'||(op==='schedule'&&prefix==='command'))){recursiveReferences.set(op+':'+prefix+':'+type.id,reference);return;}
 if(ancestors.has(type.id)||(grammar&&ancestors.has(grammar.id))){recursiveReferences.set(op+':'+prefix+':'+type.id,reference);return;}
 if(depth>6){truncatedReferences.set(op+':'+prefix+':'+type.id,reference);return;}
 const nextAncestors=new Set(ancestors);nextAncestors.add(type.id);
 // TS flattens NumericExpression into DataExpression and other union members.
 // Retain canonical grammar ancestry when all its members are present, so
 // an operand is a reference instead of another permutation of every operator.
 if(type.isUnion()){
  const members=new Set(type.types.map(t=>t.id));
  for(const grammar of recursiveGrammars)if(grammar.isUnion()&&grammar.types.every(t=>type.types.some(m=>equivalent(t,m))))nextAncestors.add(grammar.id);
 }
 if(type.isIntersection()){for(const part of type.types)describe(part,op,prefix,depth,nextAncestors);return;}
 if(type.isUnion()){for(const part of type.types)describe(part,op,prefix,depth,nextAncestors);return;}
 if(checker.isArrayType(type)||checker.isTupleType(type)){
  const element=checker.getTypeArguments(type)[0];if(element)describe(element,op,prefix+'[]',depth+1,nextAncestors);return;
 }
 if(!(type.flags&ts.TypeFlags.Object))return;
 for(const property of checker.getPropertiesOfType(type)){
  const name=property.getName();if(name==='op'||name.startsWith('__'))continue;
  const propType=checker.getTypeOfSymbolAtLocation(property,declaration);
  const substantive=propType.isUnion()?propType.types:[propType];
  if(substantive.every(t=>t.flags&(ts.TypeFlags.Never|ts.TypeFlags.Undefined)))continue;
  const key=prefix?prefix+'.'+name:name,id=op+':'+key;
  const parts=propType.isUnion()?propType.types:[propType];
  const literals=parts.flatMap(t=>t.isStringLiteral()||t.isNumberLiteral()?[t.value]:t.flags&ts.TypeFlags.BooleanLiteral?[t.intrinsicName==='true']:[]);
  const row=descriptors.get(id)||{op,field:key,types:[],choices:[]};
  row.types=[...new Set([...row.types,checker.typeToString(propType)])];row.choices=[...new Set([...row.choices,...literals])];descriptors.set(id,row);
  describe(propType,op,key,depth+1,nextAncestors);
 }
}
const declared=new Set();
for(const type of commandType.types){
 const property=type.getProperty('op');if(!property)continue;
 const opType=checker.getTypeOfSymbolAtLocation(property,declaration);
 for(const op of opType.isUnion()?opType.types:[opType])if(op.isStringLiteral()){declared.add(op.value);describe(type,op.value);}
}
function values(value,segments){
 if(!segments.length)return [value];const [head,...tail]=segments;
 if(head.endsWith('[]')){const entries=value?.[head.slice(0,-2)];return Array.isArray(entries)?entries.flatMap(v=>values(v,tail)):[];}
 return value&&Object.hasOwn(value,head)?values(value[head],tail):[];
}
// Follow compiler-declared operands; literal payloads remain opaque data.
const contextUsage=new Map(),contextSeen=new Set();
function contextualWalk(value,type,logicalPath,actualPath,root,row,depth=0){
 if(depth>64||value===null||value===undefined)return;
 const grammar=grammarOf(type),name=grammar?.aliasSymbol?.getName();
 if(name==='EventPayload')return;
 if(grammar)logicalPath=root.field;
 if(type.isUnion()||type.isIntersection()){
  for(const part of type.types)contextualWalk(value,part,logicalPath,actualPath,root,row,depth+1);
  return;
 }
 if(checker.isArrayType(type)||checker.isTupleType(type)){
  if(!Array.isArray(value))return;
  const args=checker.getTypeArguments(type);
  value.forEach((child,i)=>contextualWalk(child,args[checker.isTupleType(type)?Math.min(i,args.length-1):0],logicalPath+'[]',actualPath+'['+i+']',root,row,depth+1));
  return;
 }
 if(!(type.flags&ts.TypeFlags.Object)||typeof value!=='object'||Array.isArray(value))return;
 const known=new Set();
 for(const property of checker.getPropertiesOfType(type)){
  const key=property.getName(),propType=checker.getTypeOfSymbolAtLocation(property,declaration);
  known.add(key);if(!Object.hasOwn(value,key)||!substantive(propType))continue;
  const field=logicalPath+'.'+key,path=actualPath+'.'+key,id=row.command.op+':'+field;
  if(descriptors.has(id)){
   const observation={study:row.study,mode:row.mode,commandLocation:row.commandLocation,actualPath:path,grammar:root.grammar,value:value[key]};
   const signature=id+':'+JSON.stringify(observation);
   if(!contextSeen.has(signature)){contextSeen.add(signature);const found=contextUsage.get(id)||[];found.push(observation);contextUsage.set(id,found);}
  }
  contextualWalk(value[key],propType,field,path,root,row,depth+1);
 }
 const index=checker.getIndexTypeOfType(type,ts.IndexKind.String);
 if(index)for(const [key,child] of Object.entries(value))if(!known.has(key))
  contextualWalk(child,index,logicalPath+'.'+key,actualPath+'['+JSON.stringify(key)+']',root,row,depth+1);
}
for(const root of contextRoots.values())for(const row of usage.get(root.op)||[])
 for(const value of values(row.command,root.field.split('.')))contextualWalk(value,root.type,root.field,root.field,root,row);
const fields=[...descriptors.values()].sort((a,b)=>(a.op+':'+a.field).localeCompare(b.op+':'+b.field)).map(row=>{
 const found=(usage.get(row.op)||[]).flatMap(r=>values(r.command,row.field.split('.')).length?[r]:[]);
 const observed=rows=>rows.flatMap(r=>values(r.command,row.field.split('.'))).filter(v=>['string','number','boolean'].includes(typeof v));
 const seen=observed(found),isolatedSeen=observed(found.filter(r=>r.mode==='isolated')),applicationSeen=observed(found.filter(r=>r.mode==='application'));
 const contextualOccurrences=contextUsage.get(row.op+':'+row.field)||[];
 const contextualIsolatedCases=[...new Set(contextualOccurrences.filter(r=>r.mode==='isolated').map(r=>r.study))],contextualApplicationCases=[...new Set(contextualOccurrences.filter(r=>r.mode==='application').map(r=>r.study))];
 const contextualChoices=mode=>contextualOccurrences.filter(r=>!mode||r.mode===mode).map(r=>r.value).filter(v=>['string','number','boolean'].includes(typeof v));
 const context={contextualOccurrences,contextualIsolatedCases,contextualApplicationCases,contextStatus:contextualIsolatedCases.length&&contextualApplicationCases.length?'present-in-both':'missing-demonstration',missingContextualIsolatedChoices:row.choices.filter(v=>!contextualChoices('isolated').includes(v)),missingContextualApplicationChoices:row.choices.filter(v=>!contextualChoices('application').includes(v)),effectivePresenceStatus:(found.some(r=>r.mode==='isolated')||contextualIsolatedCases.length)&&(found.some(r=>r.mode==='application')||contextualApplicationCases.length)?'present-in-both':'missing-demonstration',missingEffectiveIsolatedChoices:row.choices.filter(v=>![...isolatedSeen,...contextualChoices('isolated')].includes(v)),missingEffectiveApplicationChoices:row.choices.filter(v=>![...applicationSeen,...contextualChoices('application')].includes(v))};
 return {...row,...context,isolatedCases:[...new Set(found.filter(r=>r.mode==='isolated').map(r=>r.study))],applicationCases:[...new Set(found.filter(r=>r.mode==='application').map(r=>r.study))],missingChoices:row.choices.filter(v=>!seen.includes(v)),missingIsolatedChoices:row.choices.filter(v=>!isolatedSeen.includes(v)),missingApplicationChoices:row.choices.filter(v=>!applicationSeen.includes(v)),status:found.some(r=>r.mode==='isolated')&&found.some(r=>r.mode==='application')?'present-in-both':'missing-demonstration',semanticAcceptance:'not-established-by-presence'};
});
const native=new Set();
for(const name of readdirSync(path.join(root,'src')).filter(n=>n.endsWith('.c'))){
 const text=readFileSync(path.join(root,'src',name),'utf8');
 for(const match of text.matchAll(/strcmp\(op,\s*"([^"]+)"\)|nrEqual\(j,\s*(?:op|nrField\(j,\s*0,\s*"op"\)),\s*"([^"]+)"\)/g))native.add(match[1]||match[2]);
}
const operationCoverage=[...declared].sort().map(op=>{
 const rows=usage.get(op)||[];
 const isolatedCases=[...new Set(rows.filter(r=>r.mode==='isolated').map(r=>r.study))];
 const applicationCases=[...new Set(rows.filter(r=>r.mode==='application').map(r=>r.study))];
 return {op,isolatedCases,applicationCases,status:isolatedCases.length&&applicationCases.length?'present-in-both':'missing-demonstration',semanticAcceptance:'not-established-by-presence'};
});
const output={contextRoots:[...contextRoots.values()].map(({type,...r})=>r),operationCoverage,scope:'Exported TypeScript direct authoring fields and finite choices, plus compiler-guided recursive operand contexts with exact source paths. Context presence does not imply valid native root guards. Field presence is not semantic acceptance; ABI methods, dynamic Record keys, native nested compiler fields and numeric range boundaries require separate coverage.',recursiveReferences:[...recursiveReferences.values()],truncatedReferences:[...truncatedReferences.values()],contractFile:'native/bindings/typescript/contracts.ts',cases:cases.length,applicationRecipes:applicationRecipes.length,declaredOperations:[...declared].sort(),nativeOperationNamesMissingFromTypes:[...native].filter(op=>!declared.has(op)).sort(),operationsWithoutCases:[...declared].filter(op=>!usage.has(op)).sort(),fields};
writeFileSync(process.argv[4],JSON.stringify(output,null,2)+'\n');
console.log(JSON.stringify({cases:cases.length,operations:declared.size,fields:fields.length,presentInBoth:fields.filter(r=>r.status==='present-in-both').length,missingTypedOperations:output.nativeOperationNamesMissingFromTypes}));
