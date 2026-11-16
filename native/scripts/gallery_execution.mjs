// Orchestration is independent of WASM; successful callbacks must finish all assertions.
export function runStudies(studies, execute, update=()=>{}) {
 const ids=studies.map(study=>study.id);
 if(!ids.length||ids.some(id=>typeof id!=='string'||!id)||new Set(ids).size!==ids.length)throw Error('Gallery requires nonempty unique case identities');
 const report={expectedCaseIds:ids,cases:[],complete:false,passed:false,status:'RUNNING'};
 update(report);
 for(const study of studies){
  const started=performance.now();let row;
  try {execute(study);row={id:study.id,status:'PASS'};}
  catch(error){row={id:study.id,status:'FAIL',errorType:error.name,error:String(error.message)};}
  row.seconds=(performance.now()-started)/1000;report.cases.push(row);update(report);
 }
 report.complete=report.cases.length===ids.length;
 report.passed=report.complete&&report.cases.every(row=>row.status==='PASS');
 report.status=report.passed?'PASS':'FAIL';update(report);return report;
}
