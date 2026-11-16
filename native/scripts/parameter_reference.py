"""Indexed authoring reference; case presence is not semantic execution coverage."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

def buildReference(root,metadata,cases):
    actual=hashlib.sha256((Path(root)/'native/bindings/typescript/contracts.ts').read_bytes()).hexdigest()
    if metadata.get('sourceSha256')!=actual:raise ValueError('Command metadata source differs')
    operations=metadata['operations']
    if len(set(operations))!=len(operations):raise ValueError('Duplicate operation')
    records={}
    for row in metadata['fields']:
        identity=(row['op'],row['field'])
        if row['op'] not in operations or identity in records:raise ValueError('Duplicate or orphan field')
        records[identity]={'id':'parameter:'+row['op']+'.'+row['field'],'operation':row['op'],
            'field':row['field'],'types':row['types'],'choices':row['choices'],'caseIds':set(),
            'explanationStatus':'Refer to component chapter; complete per-field explanation audit pending'}
    opCases={op:set() for op in operations}
    def fields(value,prefix=''):
        if isinstance(value,dict):
            for key,item in value.items():
                path=prefix+'.'+key if prefix else key
                yield path;yield from fields(item,path)
        elif isinstance(value,list):
            for item in value:yield from fields(item,prefix+'[]')
    def command(value,identity):
        if not isinstance(value,dict):return
        op=value.get('op')
        if op in opCases:
            opCases[op].add(identity)
            for field in fields(value):
                if (op,field) in records:records[op,field]['caseIds'].add(identity)
        if op=='batch':
            for child in value.get('commands',[]):command(child,identity)
        if op=='schedule':command(value.get('command'),identity)
    identities=set()
    for case in cases:
        identity=case['id']
        if identity in identities:raise ValueError('Duplicate gallery identity')
        identities.add(identity)
        for value in case.get('commands',[]):command(value,identity)
        for action in case.get('actions',[]):command(action.get('command'),identity)
    parameters=[]
    for identity,row in sorted(records.items()):
        row['caseIds']=sorted(row['caseIds']);parameters.append(row)
    return {'schema':'nocturne.parameter-reference.v1','sourceSha256':actual,'manualComplete':False,
        'semanticCoverageProven':False,'scope':'Declared types/choices and actual recipe command field presence only',
        'operations':[{'id':op,'caseIds':sorted(opCases[op])} for op in sorted(operations)],'parameters':parameters}

def markdown(reference):
    lines=['# Indexed command parameters','','This generated index preserves declared types and finite choices. Native numeric domains, defaults, coupled constraints and explanations belong to the component chapters. Their full per-field audit remains pending. Case presence is not execution or semantic coverage.','','Contract SHA256: `'+reference['sourceSha256']+'`','']
    def cell(value):return str(value).replace('|','\\|').replace('\n',' ')
    for operation in reference['operations']:
        lines+=['## '+operation['id'],'',str(len(operation['caseIds']))+' gallery recipes contain this operation.','', '| Field | Declared types | Finite choices | Recipe count |','|---|---|---|---|']
        for row in reference['parameters']:
            if row['operation']==operation['id']:
                lines.append('| `'+row['field']+'` | '+cell('; '.join(row['types']))+' | '+cell(json.dumps(row['choices'],ensure_ascii=False))+' | '+str(len(row['caseIds']))+' |')
        lines.append('')
    return '\n'.join(lines)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--json',type=Path,required=True);p.add_argument('--markdown',type=Path,required=True);a=p.parse_args()
    root=Path(__file__).resolve().parents[2];sys.path.insert(0,str(root/'native/examples'))
    from gallery_cases import build_cases
    reference=buildReference(root,json.loads((root/'native/web/workshop_fields.json').read_text()),build_cases())
    a.json.write_text(json.dumps(reference,indent=2)+'\n');a.markdown.write_text(markdown(reference))
    print(json.dumps({'operations':len(reference['operations']),'parameters':len(reference['parameters'])}))
if __name__=='__main__':main()
