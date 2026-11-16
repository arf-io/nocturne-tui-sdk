#!/usr/bin/env python3
"""Compile and execute C++17 and Python consumers of the current graph C ABI.

Writes per-command results and owned cell comparison evidence. No framework mocks,
provider coupling, Rust substitutions, or changes to the authoritative C contract.
Example: python3 native/scripts/check_graph_consumer.py
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,signal,subprocess,sys,tempfile,time,uuid
ROOT=Path(__file__).resolve().parents[1]


def newEvidenceDirectory(evidenceRoot: Path, explicit: Path | None = None) -> Path:
    """Create fresh receipt storage without replacing historical observations.

    Inputs: normal evidence root and optional explicit new destination. Output:
    the created absolute directory. Existing explicit destinations raise
    FileExistsError. Each default attempt receives its own timestamp/PID/UUID path.
    """
    out=(explicit if explicit is not None else evidenceRoot/'graph-consumer-runs'/
         (time.strftime('%Y%m%dT%H%M%S')+'-'+str(os.getpid())+'-'+uuid.uuid4().hex)).absolute()
    out.mkdir(parents=True,exist_ok=False)
    return out


def main():
    """Execute real consumers, compare cells/metadata, and return 0 or 2."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir',type=Path,help='new directory for this observation; existing paths are refused')
    args=parser.parse_args()
    out=newEvidenceDirectory(ROOT/'evidence',args.evidence_dir)
    commands=[];checks=[]
    def run(name,argv,expected=0):
        log=out/(name+'.log');start=time.monotonic();process=None
        record={'id':name,'argv':argv,'cwd':str(ROOT),'expectedExitCode':expected,'timeoutSeconds':45}
        with log.open('wb') as stream:
            try:
                process=subprocess.Popen(argv,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,
                    env=os.environ.copy(),start_new_session=os.name=='posix')
                record['childPid']=process.pid;record['exitCode']=process.wait(timeout=45)
                record['status']='PASS' if record['exitCode']==expected else 'FAIL'
            except subprocess.TimeoutExpired:
                if os.name=='posix':os.killpg(process.pid,signal.SIGKILL)
                else:process.kill()
                record.update(status='TIMEOUT',exitCode=process.wait(timeout=5))
            except OSError as error:record.update(status='BLOCKED',reason=str(error),exitCode=None)
        record.update(seconds=round(time.monotonic()-start,3),log=log.name,
            logSha256=hashlib.sha256(log.read_bytes()).hexdigest())
        commands.append(record);(out/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n')
        print(record['status'],name,record['exitCode'],flush=True)
        return record['status']=='PASS'
    with tempfile.TemporaryDirectory(prefix='nocturne-graph-consumer-') as temporary:
        tmp=Path(temporary);binary=tmp/'task-graph';cpp=tmp/'cpp.cells';python=tmp/'python'
        cxx=os.environ.get('CXX') or shutil.which('c++') or 'c++'
        library=ROOT/'dist/libnocturne_native.so'
        if sys.platform=='darwin':library=ROOT/'dist/libnocturne_native.dylib'
        build=run('cpp-build',[cxx,'-std=c++17','-Wall','-Wextra','-Werror','-Iinclude',
            'examples/task_graph.cpp','-Ldist','-lnocturne_native','-Wl,-rpath,'+str(ROOT/'dist'),'-o',str(binary)])
        cppOk=build and run('cpp-run',[str(binary),'examples/task_graph.ndjson',str(cpp)])
        pyOk=run('python-run',[sys.executable,'examples/task_graph.py','--output',str(python),'--library',str(library)])
        if cppOk and pyOk:
            checks.append({'name':'C++ and Python produce identical owned graph cells','passed':cpp.read_bytes()==(python/'graph.cells').read_bytes()})
            checks.append({'name':'C++ and Python retain identical complete native graph metadata',
                           'passed':json.loads((out/'cpp-run.log').read_text())==json.loads((python/'graph-info.json').read_text())})
            before=cpp.read_bytes()
            refused=run('cpp-refuses-existing-output',[str(binary),'examples/task_graph.ndjson',str(cpp)],expected=1)
            checks.append({'name':'rejected overwrite leaves existing cell bytes intact','passed':refused and cpp.read_bytes()==before})
            bad=tmp/'bad.ndjson';bad.write_text('{bad}\n')
            rejected=run('cpp-rejects-malformed-command',[str(binary),str(bad),str(tmp/'bad.cells')],expected=1)
            checks.append({'name':'malformed native command produces no cell artifact','passed':rejected and not (tmp/'bad.cells').exists()})
            shutil.copyfile(cpp,out/'graph.cells');shutil.copyfile(python/'graph-info.json',out/'graph-info.json')
        py2=tmp/'python2'
        if run('python-2d',[sys.executable,'examples/task_graph.py','--output',str(py2),'--dimensions','2','--library',str(library)]) and pyOk:
            checks.append({'name':'2D export uses distinct native cells with same node identities',
                'passed':(py2/'graph.cells').read_bytes()!=(python/'graph.cells').read_bytes() and
                json.loads((py2/'GRAPH.json').read_text())['nodeIds']==json.loads((python/'GRAPH.json').read_text())['nodeIds']})
    passed=bool(checks) and all(x['passed'] for x in checks) and all(x['status']=='PASS' for x in commands)
    result={'scope':'Actual C++17 C-ABI consumer and direct Python binding; not a separate C++ engine or full framework qualification.',
        'evidenceDirectory':str(out),'commands':commands,'checks':checks,'passed':passed}
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    if args.evidence_dir is None:
        (ROOT/'evidence/graph-consumer.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'checks':len(checks),'passed':passed},indent=2));return 0 if passed else 2

if __name__=='__main__':raise SystemExit(main())
