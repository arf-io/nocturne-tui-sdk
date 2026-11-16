#!/usr/bin/env python3
"""Compare every owned binding with official Unicode 17 test boundaries, offline."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from cargo_example import buildExample
ROOT=Path(__file__).resolve().parents[1]
def widthOracle():
    """Independent raw UCD sets, never the generated native tables or host wcwidth."""
    folder=ROOT/'unicode/17.0.0';wide=set();ambiguous=set();zero=set();emoji=set();variation=set();probes={0x378,0x10ffff}
    for name,target,property in [('EastAsianWidth.txt',None,None),('DerivedCoreProperties.txt',zero,'Default_Ignorable_Code_Point'),('emoji-data.txt',emoji,'Emoji_Presentation')]:
        for line in (folder/name).read_text().splitlines():
            fields=[v.strip() for v in line.split('#')[0].split(';')]
            if len(fields)<2:continue
            span=fields[0].split('..');first=int(span[0],16);last=int(span[-1],16)
            if name=='EastAsianWidth.txt':
                probes.update((first-1,first,last,last+1))
                chosen=wide if fields[1] in ('W','F') else ambiguous if fields[1]=='A' else None
            else:chosen=target if fields[1]==property else None
            if chosen is not None:chosen.update(range(first,last+1))
    for line in (folder/'UnicodeData.txt').read_text().splitlines():
        fields=line.split(';')
        if fields[2] in ('Mn','Me','Cf','Cc','Zl','Zp'):
            scalar=int(fields[0],16);zero.add(scalar);probes.add(scalar)
    for line in (folder/'emoji-variation-sequences.txt').read_text().splitlines():
        fields=line.split('#')[0].split(';')
        if len(fields)>1:variation.add(int(fields[0].split()[0],16))
    probes.update(emoji);probes.update(zero)
    def expected(record,policy):
        text=list(map(ord,record['text']));rows=[]
        for first,last in zip(record['expected'],record['expected'][1:]):
            width=0
            for i in range(first,last):
                cp=text[i]
                if cp in zero:continue
                cell=2 if cp in wide else policy if cp in ambiguous else 1
                selector=text[i+1] if i+1<last and cp in variation else None
                if selector==0xfe0f or (cp in emoji and selector!=0xfe0e):cell=2
                width=max(width,cell)
            cluster=text[first:last]
            if cluster[0] in (35,42,48,49,50,51,52,53,54,55,56,57) and (cluster[1:2]==[0x20e3] or cluster[1:3]==[0xfe0f,0x20e3]):width=2
            rows.append([first,last,width])
        return rows
    return expected,sorted(p for p in probes if 0<=p<=0x10ffff and not 0xd800<=p<=0xdfff),variation
def cases():
    folder=ROOT/'unicode/17.0.0';manifest=json.loads((folder/'SOURCES.json').read_text())
    for row in manifest['sources']:
        if hashlib.sha256((folder/row['name']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Unicode source hash mismatch')
    records=[]
    for line in (folder/'GraphemeBreakTest.txt').read_text().splitlines():
        body=line.split('#')[0].strip()
        if not body:continue
        scalars=[];expected=[]
        for word in body.split():
            if word=='÷':expected.append(len(scalars))
            elif word!='×':scalars.append(int(word,16))
        records.append({'text':''.join(map(chr,scalars)),'expected':expected})
    if len(records)!=766:raise ValueError('Unexpected official test count')
    records.extend([{'text':'','expected':[0]},{'text':'A'*2048,'expected':list(range(2049))},{'text':'A'+'\u0301'*2047,'expected':[0,2048]}]);return records

def layoutOracle(record,metrics,columns):
    """Logical rows from raw-data metric oracle, never native layout calls."""
    rows=[];column=line=0
    for first,last,width in metrics:
        scalar=ord(record['text'][first])
        if scalar in (10,13,0x85,0x2028,0x2029):
            rows.append([first,last,column,line,0]);line+=1;column=0;continue
        if scalar==9:width=min(columns,4-column%4)
        if width and column and column+width>columns:
            line+=1;column=0
            if scalar==9:width=min(4,columns)
        rows.append([first,last,column,line,width]);column+=width
    return rows

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    inputs=cases();oracle,probes,variation=widthOracle()
    inputs.extend({'text':chr(cp),'expected':[0,1]} for cp in probes)
    inputs.extend({'text':chr(cp)+chr(selector),'expected':[0,2]} for cp in sorted(variation) for selector in (0xfe0e,0xfe0f))
    inputs.extend([{'text':'❤','expected':[0,1]},{'text':'A\ufe0f','expected':[0,2]},{'text':'#\u20e3','expected':[0,2]},{'text':'A\u20e3','expected':[0,2]},{'text':'1\ufe0f\u20e3','expected':[0,3]}])
    payload=''.join(json.dumps({'text':r['text']},ensure_ascii=True,separators=(',',':'))+'\n' for r in inputs).encode();(out/'cases.ndjson').write_bytes(payload)
    rustPayload=''.join(' '.join(f'{ord(c):x}' for c in r['text'])+'\n' for r in inputs).encode();(out/'cases.rust.txt').write_bytes(rustPayload)
    with (out/'go-build.log').open('w') as log:
        subprocess.run(['go','build','-o',str(ROOT/'dist/go-graphemes'),'./cmd/graphemes'],cwd=ROOT/'bindings/go',check=True,stdout=log,stderr=subprocess.STDOUT)
    rust=buildExample(ROOT/'bindings/rust/Cargo.toml','graphemes',out/'rust-build.log',release=True)
    runners={'python':[sys.executable,str(ROOT/'scripts/graphemes.py')],'typescript':['node',str(ROOT/'scripts/graphemes.mjs')],'go':[str(ROOT/'dist/go-graphemes')],'rust':[str(rust)]}
    results={};mismatches=[]
    for name,argv in runners.items():
        r=subprocess.run(argv,input=rustPayload if name=='rust' else payload,capture_output=True,timeout=90);(out/(name+'.jsonl')).write_bytes(r.stdout);(out/(name+'.stderr')).write_bytes(r.stderr)
        rows=[json.loads(line) for line in r.stdout.splitlines()] if r.returncode==0 else []
        passed=r.returncode==0 and len(rows)==len(inputs)
        for i,(expected,actual) in enumerate(zip(inputs,rows)):
            if actual.get('index')!=i or actual.get('boundaries')!=expected['expected']:mismatches.append({'runtime':name,'case':i,'expected':expected['expected'],'actual':actual});passed=False
            for policy in (1,2):
                widths=oracle(expected,policy)
                if actual.get('widths'+str(policy))!=widths:mismatches.append({'runtime':name,'case':i,'policy':policy,'expected':widths,'actual':actual});passed=False
            layouts=[layoutOracle(expected,oracle(expected,policy),columns) for columns in (1,3,8) for policy in (1,2)]
            if actual.get('layouts')!=layouts:mismatches.append({'runtime':name,'case':i,'expectedLayouts':layouts,'actual':actual});passed=False
        results[name]={'status':'PASS' if passed else 'FAIL','records':len(rows),'exitCode':r.returncode}
    report={'scope':'Unicode 17 UAX29-47 segmentation, nr-grapheme-cell-width-v1 metrics and nr-grapheme-layout-v1 logical rows through four owned bindings; raw UCD oracle, both ambiguous policies; no geometry/bidi/shaping claim','layoutColumns':[1,3,8],'layoutPolicies':[1,2],'unicodeVersion':'17.0.0','officialCases':766,'boundaryCases':3,'metricCases':len(inputs)-769,'inputSha256':hashlib.sha256(payload).hexdigest(),'rustInputSha256':hashlib.sha256(rustPayload).hexdigest(),'results':results,'mismatches':mismatches,'passed':all(r['status']=='PASS' for r in results.values()) and not mismatches}
    (out/'RESULTS.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
    if not report['passed']:raise SystemExit(2)
if __name__=='__main__':main()
