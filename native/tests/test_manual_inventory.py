import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import manual_inventory

class ManualInventory(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'native/bindings/typescript').mkdir(parents=True)
        (self.root/'native/bindings/typescript/contracts.ts').write_text('export type Test = number;\n')
        (self.root/'native/catalogue.json').write_text(json.dumps([{'id':'text/fade','name':'Fade','contract':'TextTransition'}]))
        for path in ('native/include/nocturne_native.h','native/hosts/python/prompt_toolkit_host.py',
                     'native/hosts/terminal-kit/host.mjs','native/hosts/bubbletea/main.go','native/hosts/ratatui/src/lib.rs'):
            target=self.root/path;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text('int nrInfo(void);\n' if path.endswith('.h') else 'Interface fixture source\n')
        self.authoring={'declaredOperations':['widget','accessibility'],'fields':[{'op':'widget','field':'alpha','types':['number'],'choices':[]},{'op':'accessibility','field':'reducedMotion','types':['boolean'],'choices':[False,True]}]}

    def testExactDeterministicInventoryAndTruthfulMissingEvidence(self):
        out=manual_inventory.buildInventory(self.root,self.authoring)
        self.assertEqual([x['id'] for x in out['operations']],['operation:accessibility','operation:widget'])
        self.assertEqual([x['id'] for x in out['parameters']],['parameter:accessibility.reducedMotion','parameter:widget.alpha'])
        self.assertEqual(out['components'][0]['id'],'component:text/fade')
        self.assertFalse(out['manualComplete']);self.assertFalse(out['workshopComplete'])
        self.assertTrue(all(x['missingEvidence'] for group in ('operations','parameters','components') for x in out[group]))
        reordered=copy.deepcopy(self.authoring);reordered['declaredOperations'].reverse();reordered['fields'].reverse()
        self.assertEqual(out,manual_inventory.buildInventory(self.root,reordered))
        manual_inventory.validateSource(out,self.root)

    def testActualSourceMutationRejectsStaleInventory(self):
        out=manual_inventory.buildInventory(self.root,self.authoring)
        (self.root/'native/bindings/typescript/contracts.ts').write_text('export type Test = string;\n')
        with self.assertRaises(ValueError):manual_inventory.validateSource(out,self.root)

    def testDuplicateAndOrphanAuthoringInputsReject(self):
        for kind in ('operation','field','orphan'):
            value=copy.deepcopy(self.authoring)
            if kind=='operation':value['declaredOperations'].append('widget')
            elif kind=='field':value['fields'].append(value['fields'][0])
            else:value['fields'][0]['op']='unknown'
            with self.subTest(kind=kind),self.assertRaises(ValueError):manual_inventory.buildInventory(self.root,value)

    def testDuplicateCatalogueIdentitiesReject(self):
        p=self.root/'native/catalogue.json';row=json.loads(p.read_text())[0];p.write_text(json.dumps([row,row]))
        with self.assertRaises(ValueError):manual_inventory.buildInventory(self.root,self.authoring)

if __name__=='__main__':unittest.main()
