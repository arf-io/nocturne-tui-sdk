"""Inventory manual/workshop subjects; evidence presence is not semantic review."""
from pathlib import Path
import argparse
import hashlib
import json
import re

HOSTS={'prompt-toolkit':'native/hosts/python/prompt_toolkit_host.py',
       'terminal-kit':'native/hosts/terminal-kit/host.mjs',
       'bubbletea':'native/hosts/bubbletea/main.go','ratatui':'native/hosts/ratatui/src/lib.rs'}
SOURCES=('native/bindings/typescript/contracts.ts','native/catalogue.json',
         'native/include/nocturne_native.h',*HOSTS.values())
REQUIREMENTS=('explanation','defaults','constraintsAndUnits','lifecycle','rejectionBehavior',
              'standaloneExample','applicationExample','screenshot','video',
              'workshopConfiguration','compositeExample','validatedExportRoundtrip')

def sourceHashes(root):
    result={}
    for name in SOURCES:
        path=Path(root)/name
        if path.is_symlink() or not path.is_file():raise ValueError('Missing regular source: '+name)
        result[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return result

def validateSource(inventory,root):
    if inventory.get('sources')!=sourceHashes(root):raise ValueError('Manual inventory source changed')

def unique(values,label):
    if any(not isinstance(x,str) or not x for x in values) or len(set(values))!=len(values):
        raise ValueError('Invalid or duplicate '+label)

def subject(identity,**fields):
    return {'id':identity,**fields,'missingEvidence':list(REQUIREMENTS)}

def abiDeclarations(header):
    clean=re.sub(r'/\*.*?\*/|//[^\n]*','',header,flags=re.S)
    pattern=r'^[ \t]*((?:const[ \t]+)?[A-Za-z_]\w*[ \t]*(?:\*[ \t]*)?(nr[A-Za-z0-9_]+)[ \t]*\([^;{}]*\)[ \t]*;)'
    rows=[{'name':m.group(2),'signature':' '.join(m.group(1).split())}
          for m in re.finditer(pattern,clean,re.M)]
    unique([row['name'] for row in rows],'ABI methods')
    if not rows:raise ValueError('No public ABI declarations')
    return sorted(rows,key=lambda x:x['name'])

def buildInventory(root,authoring):
    sources=sourceHashes(root)
    operations=authoring['declaredOperations'];unique(operations,'operations')
    parameters=[]
    for row in authoring['fields']:
        if row['op'] not in operations:raise ValueError('Orphan parameter operation')
        if not isinstance(row['field'],str) or not row['field']:raise ValueError('Invalid parameter field')
        parameters.append(subject('parameter:'+row['op']+'.'+row['field'],operation=row['op'],
                                  field=row['field'],types=row['types'],choices=row['choices']))
    unique([x['id'] for x in parameters],'parameters')
    catalogue=json.loads((Path(root)/'native/catalogue.json').read_text())
    unique([x['id'] for x in catalogue],'components')
    return {'schema':'nocturne.manual-inventory.v1','sources':sources,
            'scope':'Public authoring operations/fields and catalogue identities; coverage leads only',
            'operations':[subject('operation:'+op,operation=op) for op in sorted(operations)],
            'parameters':sorted(parameters,key=lambda x:x['id']),
            'components':[subject('component:'+x['id'],component=x['id'],name=x['name'],contract=x['contract'])
                          for x in sorted(catalogue,key=lambda x:x['id'])],
            'abiMethods':[subject('abi:'+row['name'],**row) for row in
                          abiDeclarations((Path(root)/'native/include/nocturne_native.h').read_text())],
            'hosts':[subject('host:'+host,host=host,source=source) for host,source in sorted(HOSTS.items())],
            'additionalInventoryRequired':['recursive grammars','dynamic record keys',
                                           'numeric domains and defaults','host method semantics'],
            'manualComplete':False,'workshopComplete':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--authoring',type=Path,required=True,help='Fresh gallery_option_coverage.mjs output')
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2])
    a=p.parse_args();inventory=buildInventory(a.root,json.loads(a.authoring.read_text()))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(inventory,indent=2)+'\n')
    print(json.dumps({k:len(inventory[k]) for k in ('operations','parameters','components','abiMethods','hosts')}))

if __name__=='__main__':main()
