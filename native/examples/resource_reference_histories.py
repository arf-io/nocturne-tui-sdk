"""Model public operation histories rather than assuming all writes idempotent."""
import copy
def repair_reference_histories(cases):
    result=[]
    for original in cases:
        family=original['demonstrates']['family'];field=original['demonstrates']['field']
        kind=original['commands'][-1].get('type','number')
        affected=family=='text' or (kind=='string' and family in ('window','widget','node','indicator')) or (family in ('floor','surface') and field=='overflow') or (family=='emitter' and (field.startswith('extent.') or field=='sampling'))
        if not affected:result.append(original);continue
        case=copy.deepcopy(original);value=case['actions'][0]['command']['value']
        if family in ('floor','surface') and field=='overflow':
            owner=next(c for c in reversed(case['baselineCommands']) if c['op']==family)
            owner['overflow']='merge-to-field';value=0
            for action in case['actions']:
                if action['command']['op']=='set' and action['command'].get('value')==1:action['command']['value']=value
                if action['expectedInfo']['values']['/ownership/control']==1:action['expectedInfo']['values']['/ownership/control']=value
            edit={'op':family,'overflow':'reject-new'}
            if family=='surface':edit['id']=1
            case['referenceCommands']=copy.deepcopy(case['baselineCommands'])+[edit]
        elif family=='emitter':
            owner=next(c for c in reversed(case['baselineCommands']) if c['op']=='emitter' and c['id']==1)
            if field=='sampling':owner['sampling']='cell'
            else:owner['extent']['xyz'.index(field[-1])]=0
        elif family=='text' and field=='material':
            case['referenceCommands']=copy.deepcopy(case['baselineCommands'])
            owner=next(c for c in case['referenceCommands'] if c['op']=='text' and c['id']==1);owner['material']=value
        else:
            if family=='text' and kind=='number':
                edit=next(copy.deepcopy(c) for c in reversed(case['referenceCommands']) if c['op']=='text' and c.get('id')==1)
            else:edit={'op':family,'id':1,field:value}
            case['referenceCommands']=copy.deepcopy(case['baselineCommands'])+[edit]
            case['referenceReapplyCommands']=[copy.deepcopy(edit)]
        case['commands']=copy.deepcopy(case['baselineCommands'])+[copy.deepcopy(original['commands'][-1])]
        result.append(case)
    return result
