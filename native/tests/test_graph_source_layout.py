"""Run the retained original LayoutJob, never a reimplementation oracle."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
import copy,json,math,subprocess,tempfile,unittest
from pathlib import Path
from native.bindings.python.nocturne_native import NativeScene
ROOT=Path(__file__).resolve().parents[1]
NODES=[1,2,3,10,11,12,20]
EDGES=[(1,2),(1,3),(2,10),(3,10),(10,11),(11,12),(12,11)]
def commands(options):
    return [{'op':'node','id':i,'label':'NODE '+str(i)} for i in NODES]+[{'op':'edge','from':a,'to':b} for a,b in EDGES]+[{'op':'layout','profile':'source',**options}]
def options():
    base={'seed':2030,'nodeGap':14,'layerGap':17,'depthGap':4,'orientation':'LR'}
    result=[{**base,'mode':mode,'dimensions':d,'iterations':19} for mode in ('layered','force','radial') for d in (2,3)]
    result += [{**base,'mode':'layered','dimensions':3,'nodeGap':v,'layerGap':v+1,'depthGap':v,'sweeps':s,'orientation':o} for v,s,o in ((.5,0,'TB'),(40,24,'LR'))]
    result += [{**base,'mode':'force','dimensions':3,'iterations':21,'repulsion':0,'spring':.7,'linkLength':5,'damping':.5,'timeStep':.1,'collision':0}, {**base,'mode':'force','dimensions':3,'iterations':0,'seed':4294967295}]
    return result
class SourceGraphLayout(unittest.TestCase):
    def test_all_original_layout_modes_and_controls(self):
        requests=[{'graph':{'nodes':[{'id':str(i),'label':'NODE '+str(i)} for i in NODES],'edges':[{'source':str(a),'target':str(b)} for a,b in EDGES]},'options':{k:v for k,v in o.items() if k!='dimensions'}|{'mode':o['mode']+'-'+str(o['dimensions'])+'d'}} for o in options()]
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'in.json';b=Path(d)/'out.json';a.write_text(json.dumps(requests));subprocess.run(['node',str(ROOT/'tests/original_graph_layout_oracle.mjs'),str(a),str(b)],check=True);expected=json.loads(b.read_text())
        for o,result in zip(options(),expected):
            with self.subTest(options=o),NativeScene(2030) as scene:
                for c in commands(o):scene.command(c)
                scene.advance_to(800000);actual={str(n['id']):n for n in scene.info()['nodes']}
                for n in result['nodes']:
                    for a,b in zip(actual[n['id']]['position'],(n['x'],n['y'],-n['z'])):self.assertAlmostEqual(a,b,places=5)
                self.assertEqual(len(actual),len(NODES));self.assertEqual(len(scene.info()['graph']['edges']),len(EDGES))
    def test_all_controls_readback_snapshot_relayout_and_custom_geometry(self):
        chosen={'mode':'force','dimensions':3,'seed':41,'iterations':5,'nodeGap':7,'layerGap':13,'depthGap':9,'repulsion':90,'spring':.2,'linkLength':11,'damping':.6,'timeStep':.2,'sweeps':4,'collision':.7,'orientation':'TB','nodeSizes':[{'id':1,'width':9,'height':4}],'edgeWeights':[{'from':1,'to':2,'kind':'contains','weight':2.5}]}
        with NativeScene() as scene:
            for c in commands(chosen):scene.command(c)
            state=scene.info()['graph'];self.assertEqual(state['layoutProfile'],'source');actual=state['sourceLayout']
            for k,v in chosen.items():
                if k not in ('nodeSizes','edgeWeights'):self.assertEqual(actual[k],v)
            self.assertIn(chosen['nodeSizes'][0],actual['nodeSizes']);self.assertIn(chosen['edgeWeights'][0],actual['edgeWeights'])
            snapshot=scene.snapshot();scene.command({'op':'layout','dimensions':2});scene.restore(snapshot);self.assertEqual(scene.info()['graph'],state)
            scene.command({'op':'layout','profile':'source','iterations':0});again=scene.info()['graph']['sourceLayout'];self.assertEqual(again['repulsion'],90);self.assertEqual(again['seed'],41);self.assertEqual(again['iterations'],0)
    def test_full_pool_original_geometry_weights_pins_and_wasm_parity(self):
        requests=[];cases=[]
        for count,mode,dims in [(64,'force',3),(13,'radial',2),(8,'layered',3)]:
            ids=list(range(1,count+1));edges=[(i,i+1)for i in ids[:-1]]+[(1,2)]
            nodes=[{'id':str(i),'width':3+i%6,'height':2+i%3,**({'pin':{'x':-7,'y':4,'z':5}}if i==4 else {})}for i in ids]
            links=[{'source':str(a),'target':str(b),'weight':.3+(k%5)}for k,(a,b)in enumerate(edges)];o={'mode':mode,'dimensions':dims,'iterations':17,'seed':4294967295,'nodeGap':14,'layerGap':17,'depthGap':4,'orientation':'LR'}
            cs=[{'op':'node','id':i,'label':'NODE '+str(i),**({'pinned':True,'position':[-7,4,-5]}if i==4 else {})}for i in ids]+[{'op':'edge','from':a,'to':b,'kind':'related'if k==len(edges)-1 else 'contains'}for k,(a,b)in enumerate(edges)]
            cs.append({'op':'layout','profile':'source',**o,'nodeSizes':[{'id':int(x['id']),'width':x['width'],'height':x['height']}for x in nodes],'edgeWeights':[{'from':a,'to':b,'kind':'related'if k==len(edges)-1 else 'contains','weight':links[k]['weight']}for k,(a,b)in enumerate(edges)]})
            requests.append({'graph':{'nodes':nodes,'edges':links},'options':{k:v for k,v in o.items()if k!='dimensions'}|{'mode':mode+'-'+str(dims)+'d'}});cases.append({'id':str(count),'commands':cs,'timeUs':900000})
        with tempfile.TemporaryDirectory()as folder:
            p=Path(folder);(p/'in.json').write_text(json.dumps(requests));subprocess.run(['node',str(ROOT/'tests/original_graph_layout_oracle.mjs'),str(p/'in.json'),str(p/'reference.json')],check=True);expected=json.loads((p/'reference.json').read_text())
            (p/'in.json').write_text(json.dumps(cases));subprocess.run(['node',str(ROOT/'tests/spatial_contract_wasm.mjs'),str(p/'in.json'),str(p/'wasm.json')],check=True);wasm=json.loads((p/'wasm.json').read_text())
        for case,reference,w in zip(cases,expected,wasm):
            with self.subTest(case=case['id']),NativeScene(2030)as scene:
                for c in case['commands']:scene.command(c)
                scene.advance_to(case['timeUs']);scene.render();native=scene.info();actual={str(n['id']):n for n in native['nodes']}
                for node in reference['nodes']:
                    for a,b in zip(actual[node['id']]['position'],(node['x'],node['y'],-node['z'])):self.assertAlmostEqual(a,b,places=5)
                self.assertEqual(native,w['info']);self.assertEqual(list(memoryview(scene.render().bytes).cast('I')),w['words'])
    def test_parser_bounds_atomicity_and_existing_measured_layout(self):
        with NativeScene(2030) as scene:
            for c in commands({'dimensions':3,'mode':'layered'}):scene.command(c)
            saved=scene.snapshot()
            for patch in [{'nodeGap':0},{'depthGap':81},{'iterations':801},{'seed':-1},{'seed':1.5},{'orientation':'ZZ'},{'timeStep':0},{'damping':1},{'sweeps':25},{'collision':2},{'unexpected':1},{'nodeSizes':[{'id':999,'width':5}]}]:
                with self.assertRaises(ValueError):scene.command({'op':'layout','profile':'source',**patch})
                self.assertEqual(scene.snapshot(),saved)
            scene.command({'op':'layout','dimensions':2,'mode':'layered','spacing':30});self.assertEqual(scene.info()['graph']['dimensions'],2)
if __name__=='__main__':unittest.main()
