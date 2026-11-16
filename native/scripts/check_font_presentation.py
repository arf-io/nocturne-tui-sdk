#!/usr/bin/env python3
"""Execute the external-font presentation example and retain actual artifacts.

Unit contracts run in python-contracts. This step exercises the consuming example
with real caller-owned font/library bytes, and does not install dependencies.
"""
from pathlib import Path
import hashlib,json,os,subprocess,sys,tempfile
import xml.etree.ElementTree as E
from delivery_runner import atomicJson

ROOT=Path(__file__).resolve().parents[1]
NS='{http://www.w3.org/2000/svg}'

def fixtures(environment):
    result={}
    for name in ['NOCTURNE_HARFBUZZ_LIBRARY','NOCTURNE_SHAPING_FONT']:
        value=environment.get(name)
        if not value:raise ValueError('Required external presentation fixture: '+name)
        path=Path(value).resolve(strict=True)
        if not path.is_file():raise ValueError('Fixture must be an explicit file: '+name)
        result[name]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
    return result

def main():
    output=ROOT/'evidence/font-presentation'
    if output.is_symlink():raise ValueError('Presentation output cannot be a symlink')
    output.mkdir(parents=True,exist_ok=True)
    report={'schema':'nocturne.font-presentation.v1','passed':False,'status':'RUNNING','scope':'Explicit external-font Python host shaping and SVG example, manual and native script spans; no browser, contour-hit or platform-font acceptance'}
    atomicJson(output/'RESULTS.json',report)
    try:
        environment=dict(os.environ);before=fixtures(environment);report['fixtures']=before
        with tempfile.TemporaryDirectory(prefix='.font-presentation-',dir=output) as temporary:
            temp=Path(temporary);runs=[];geometries=[]
            for index in range(16):
                target=temp/f'run-{index}.svg'
                argv=[sys.executable,str(ROOT/'examples/font_presentation.py'),'--library',before['NOCTURNE_HARFBUZZ_LIBRARY']['path'],'--font',before['NOCTURNE_SHAPING_FONT']['path'],'--output',str(target),'--select','10','13','--alpha','0.75']
                if index>=2:argv.append('--automatic-scripts')
                if index>=4:argv.extend(['--wrap-width','96' if 10<=index<12 else '240','--geometry-output',str(temp/f'geometry-{index}.json'),'--hit','-1','48'])
                if 6<=index<8:argv.extend(['--break-opportunities','9','16','19','24','32','37','49'])
                if index>=8:argv.extend(['--break-policy','unicode'])
                if 10<=index<12:argv.extend(['--overflow-policy','overflow'])
                if index>=12:argv.extend(['--alignment','center' if index<14 else 'right'])
                run=subprocess.run(argv,cwd=ROOT,env=environment,capture_output=True,timeout=120)
                (output/f'example-{index}.stdout').write_bytes(run.stdout);(output/f'example-{index}.stderr').write_bytes(run.stderr)
                if run.returncode:raise RuntimeError(f'Presentation example {index} failed with exit {run.returncode}')
                runs.append(target.read_bytes())
                if index>=4:geometries.append((temp/f'geometry-{index}.json').read_bytes())
            if any(runs[index]!=runs[index+1] for index in range(0,16,2)):raise ValueError('Repeated presentation differs')
            if runs[0]!=runs[2]:raise ValueError('Automatic script presentation differs from explicit reference')
            root=E.fromstring(runs[0]);paths=root.findall('.//'+NS+'path');parts=root.findall(NS+'svg')
            if not paths or len(parts)<3:raise ValueError('Missing actual multi-line glyph presentation')
            levels=[int(part.attrib['data-level']) for part in parts]
            if not any(level&1 for level in levels) or not any(not level&1 for level in levels):raise ValueError('Missing mixed-direction presentation')
            selection=root.find(NS+'g')
            if selection is None or selection.attrib.get('data-selection')!='ink' or not selection.findall(NS+'rect'):raise ValueError('Missing real selection painting')
            for path in paths:
                if not path.attrib.get('d') or int(path.attrib['data-glyph'])<=0 or not json.loads(path.attrib['data-identities']):raise ValueError('Invalid glyph or retained mapping')
            if fixtures(environment)!=before:raise ValueError('External font/library changed during presentation')
            data=runs[0];(output/'screen.svg').write_bytes(data)
            (output/'automatic-screen.svg').write_bytes(runs[2])
            wrapped=E.fromstring(runs[4]);wrappedParts=wrapped.findall(NS+'svg')
            wrappedLines=sorted(set(int(part.attrib['data-line']) for part in wrappedParts))
            if len(wrappedLines)<=3 or not wrapped.findall('.//'+NS+'path'):raise ValueError('Missing actual font-wrapped presentation')
            if geometries[0]!=geometries[1]:raise ValueError('Repeated owned geometry differs')
            geometry=json.loads(geometries[0]);viewport=geometry['viewport']
            if geometry['hit']['ink'] is not None or geometry['hit']['edge'] is not None:raise ValueError('Clipped viewport captured outside pointer')
            if not geometry['ink'] or not geometry['edges']:raise ValueError('Missing actual interaction geometry')
            for region in geometry['ink']:
                if not viewport[0]<=region['left']<region['right']<=viewport[2] or not viewport[1]<=region['top']<region['bottom']<=viewport[3]:raise ValueError('Ink geometry outside viewport')
                if not region['identities'] or not 0<=region['start']<region['end']<=len(geometry['source']):raise ValueError('Interaction geometry lost source ownership')
            if fixtures(environment)!=before:raise ValueError('External font/library changed during wrapped presentation')
            (output/'wrapped-screen.svg').write_bytes(runs[4])
            (output/'wrapped-geometry.json').write_bytes(geometries[0])
            if geometries[2]!=geometries[3]:raise ValueError('Repeated break-aware geometry differs')
            preferred=json.loads(geometries[2]);wrapping=preferred['wrapping']
            if wrapping['breakOpportunities']!=[9,16,19,24,32,37,49] or 9 not in wrapping['lineEnds']:raise ValueError('Preferred source break missing from actual layout')
            if wrapping['lineEnds']==geometry['wrapping']['lineEnds']:raise ValueError('Break-aware presentation failed to exercise the supplied policy')
            if len(wrapping['lineWidths'])!=len(wrapping['lineEnds']) or wrapping['lineEnds'][-1]!=len(preferred['source']):raise ValueError('Incomplete measured source layout')
            if preferred['source']!=geometry['source'] or preferred['fonts']!=geometry['fonts']:raise ValueError('Break policy changed source or font provenance')
            if preferred['hit']['ink'] is not None or preferred['hit']['edge'] is not None:raise ValueError('Break-aware viewport captured outside pointer')
            (output/'preferred-break-screen.svg').write_bytes(runs[6]);(output/'preferred-break-geometry.json').write_bytes(geometries[2])
            if geometries[4]!=geometries[5]:raise ValueError('Repeated Unicode geometry differs')
            unicodeGeometry=json.loads(geometries[4]);unicodeWrapping=unicodeGeometry['wrapping']
            if unicodeWrapping['breakPolicy']!='unicode' or unicodeWrapping['breakOpportunities'] is not None:raise ValueError('Unicode policy not exercised')
            if unicodeGeometry['source']!=geometry['source'] or unicodeGeometry['fonts']!=geometry['fonts']:raise ValueError('Unicode layout changed source or fonts')
            if unicodeWrapping['lineEnds'][-1]!=len(unicodeGeometry['source']) or len(unicodeWrapping['lineWidths'])!=len(unicodeWrapping['lineEnds']):raise ValueError('Incomplete Unicode layout')
            if len(unicodeWrapping['lineEnds'])<=3 or 9 not in unicodeWrapping['lineEnds']:raise ValueError('Unicode example did not exercise word wrapping')
            if unicodeGeometry['hit']['ink'] is not None or unicodeGeometry['hit']['edge'] is not None:raise ValueError('Unicode viewport captured outside pointer')
            (output/'unicode-break-screen.svg').write_bytes(runs[8]);(output/'unicode-break-geometry.json').write_bytes(geometries[4])
            if geometries[6]!=geometries[7]:raise ValueError('Repeated intact-word overflow differs')
            overflow=json.loads(geometries[6]);overflowWrapping=overflow['wrapping']
            if overflowWrapping['overflowPolicy']!='overflow' or not overflowWrapping['overflowLines']:raise ValueError('Intact overflow not exercised')
            if overflow['source']!=geometry['source'] or overflow['fonts']!=geometry['fonts']:raise ValueError('Intact overflow changed source or fonts')
            for line in overflowWrapping['overflowLines']:
                if overflowWrapping['lineWidths'][line]<=96:raise ValueError('Overflow lacks measured width evidence')
            (output/'intact-word-screen.svg').write_bytes(runs[10]);(output/'intact-word-geometry.json').write_bytes(geometries[6])
            for index,factor,name in [(12,.5,'center'),(14,1,'right')]:
                offset=index-4
                if geometries[offset]!=geometries[offset+1]:raise ValueError('Repeated aligned geometry differs')
                aligned=json.loads(geometries[offset])
                if aligned['wrapping']!=unicodeWrapping or aligned['source']!=unicodeGeometry['source'] or aligned['fonts']!=unicodeGeometry['fonts']:raise ValueError('Alignment changed shaping policy or provenance')
                if len(aligned['edges'])!=len(unicodeGeometry['edges']):raise ValueError('Alignment lost source edges')
                for edge,reference in zip(aligned['edges'],unicodeGeometry['edges']):
                    for key in ['offset','line','level','identities','baseline','affinity']:
                        if edge[key]!=reference[key]:raise ValueError('Alignment changed source mapping')
                    expected=reference['x']+factor*(944-unicodeWrapping['lineWidths'][edge['line']])
                    if abs(edge['x']-expected)>1e-7:raise ValueError('Alignment differs from independent advance reference')
                if aligned['hit']['ink'] is not None or aligned['hit']['edge'] is not None:raise ValueError('Aligned viewport captured outside pointer')
                (output/f'{name}-screen.svg').write_bytes(runs[index]);(output/f'{name}-geometry.json').write_bytes(geometries[offset])
            report.update(passed=True,status='PASS',svgSha256=hashlib.sha256(data).hexdigest(),glyphPaths=len(paths),visualRuns=len(parts),levels=levels,deterministic=True,automaticMatchesExplicit=True,wrappedSvgSha256=hashlib.sha256(runs[4]).hexdigest(),wrappedLines=wrappedLines)
            report.update(preferredBreakSvgSha256=hashlib.sha256(runs[6]).hexdigest(),preferredBreakLineEnds=wrapping['lineEnds'],unicodeBreakSvgSha256=hashlib.sha256(runs[8]).hexdigest(),unicodeBreakLineEnds=unicodeWrapping['lineEnds'],intactOverflowLines=overflowWrapping['overflowLines'],alignmentReferences=['center','right'],exampleRuns=16)
    except Exception as error:
        report.update(status='FAIL',reason=str(error))
    atomicJson(output/'RESULTS.json',report)
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 2

if __name__=='__main__':raise SystemExit(main())
