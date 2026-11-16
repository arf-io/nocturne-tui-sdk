"""Source-derived world nova optical references in paired retained scenes."""
import copy,math
from world_shell_studies import build_world_shell_studies
def hash32(v):
    v&=0xffffffff;v=((v^(v>>16))*0x7feb352d)&0xffffffff;v=((v^(v>>15))*0x846ca68b)&0xffffffff;return v^(v>>16)
def build_world_nova_optics_studies():
    cases=[]
    for source in build_world_shell_studies():
        if 'clumpy-fibonacci' not in source['id']:continue
        case=copy.deepcopy(source);case['id']=case['id'].replace('world-shell-','world-nova-optics-');case['name']=case['name'].replace('World shells','World nova optics');case['demonstrates']={'feature':'world-nova-optics'}
        samples=[]
        for i in range(16):
            lat=1-2*(i+.5)/64;angle=i*2.399963229728653+73*.0001;clump=.3+.7*math.sin(2*angle+lat*9+73)**2
            a=hash32(73^(((i*4+1)*0x9e3779b1)&0xffffffff))/4294967296
            samples.append([i+1,73,64,i,250000,clump,clump,25+260*.25/5+60*a])
        case['actions'][0]['expectedApproxInfo']={'emitters':[{'novaOptics':{'samples':samples}}]}
        case['actions'][0]['expectedInfo']['emitters'][0]['novaOptics']={'sampleLimit':16,'activeCapturedParticles':64}
        cases.append(case)
    return cases
