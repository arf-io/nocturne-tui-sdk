"""Runtime discovery agrees with the actual wire writer and owned metadata."""
import sys, pathlib; _REPOSITORY_ROOT = str(pathlib.Path(__file__).resolve().parents[2]); _REPOSITORY_ROOT in sys.path or sys.path.insert(0, _REPOSITORY_ROOT)  # native.* imports from any working directory: native/scripts/repository_root_bootstrap.py
from native.tests.current_writer_contract import current_schema, snapshot_size
from pathlib import Path
import sys,unittest,struct,gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
class RuntimeContract(unittest.TestCase):
 def test_legacy_import_reports_promoted_live_state_without_rewriting_input(self):
  fixture=ROOT/'tests/fixtures/schema-20261031-before-trigger-formulas.snapshot'
  original=gzip.decompress(fixture.with_suffix('.snapshot.gz').read_bytes())
  manifest=json.loads(fixture.with_suffix('.snapshot.json').read_text())
  self.assertEqual(hashlib.sha256(original).hexdigest(),manifest['snapshotSha256'])
  self.assertEqual(struct.unpack_from('<I',original,12)[0],0x20261031)
  supplied=bytearray(original)
  with NativeScene(42) as s:
   s.restore(supplied);self.assertEqual(supplied,original)
   promoted=s.snapshot();contract=s.info()['contract']
   self.assertEqual(contract['snapshotSchema'],current_schema())
   self.assertEqual(contract['sourceSchema'],current_schema())
   self.assertEqual(contract['sourceSchema'],struct.unpack_from('<I',promoted,28)[0])
   self.assertEqual(contract['snapshotCapacityBytes'],len(promoted))
   s.restore(promoted);self.assertEqual(s.info()['contract'],contract)
   self.assertEqual(s.snapshot(),promoted)
 def test_discovery_matches_wire_header_and_queries_are_owned(self):
  with NativeScene(42) as s:
   saved=s.snapshot();contract=s.info()['contract']
   self.assertEqual(contract['abiVersion'],struct.unpack_from('<I',saved,8)[0])
   self.assertEqual(contract['snapshotSchema'],struct.unpack_from('<I',saved,12)[0])
   self.assertEqual(contract['sourceSchema'],struct.unpack_from('<I',saved,28)[0])
   self.assertEqual(contract['snapshotCapacityBytes'],len(saved))
   self.assertEqual(contract['metadataProfile'],'nocturne.metadata/v1')
   self.assertEqual(contract['commandProfile'],'nocturne.commands/v1')
   self.assertEqual(len(contract['bindingFamilies']),24)
   self.assertEqual(len(set(contract['bindingFamilies'])),24)
   self.assertIn('accessibility',contract['bindingFamilies']);self.assertIn('character-cell-inspection',contract['features'])
   for feature in ['thermal-cell-inspection','thermal-response-settings','thermal-value-bindings','shortcut-negotiation']:self.assertIn(feature,contract['features'])
   self.assertIn('unicode-line-breaks',contract['features'])
   for name,words,unit,fields in [('nrLineBreaks',1,'offset',['offset']),('nrLineBreakDetails',2,'row',['offset','mandatory'])]:
    query=contract['queryContracts'][name]
    self.assertEqual(query['rowWords'],words);self.assertEqual(query['capacityUnit'],unit);self.assertEqual(query['fields'],fields)
    self.assertEqual(query['alignmentBytes'],4);self.assertEqual(query['maxSourceScalars'],2048);self.assertEqual(query['profile'],'unicode-17.0.0-uax14-55-default');self.assertEqual(query['offsetUnit'],'unicode-scalar')
    for flag in ['ownedBindings','pure','invalidOutputUnchanged','inputOutputAliasAllowed','nullOutputSizeProbe','endOfTextIncluded']:self.assertTrue(query[flag])
   self.assertEqual(contract['queryContracts']['nrLineBreakDetails']['mandatoryValues'],[0,1])
   thermal=contract['queryContracts']['nrThermalSample']
   for feature in ['water-cell-inspection','water-volume-authoring','water-response-settings','water-value-bindings']:self.assertIn(feature,contract['features'])
   water=contract['queryContracts']['nrWaterSample'];self.assertEqual(water['rowWords'],8);self.assertEqual(water['capacityUnit'],'double');self.assertTrue(water['pure']);self.assertTrue(water['ownedBindings'])
   self.assertEqual(water['fields'],['surfaceId','receivedVolume','retainedVolume','wetness','importedVolume','transferredVolume','evaporatedVolume','capacity'])
   self.assertEqual(thermal['capacityUnit'],'double');self.assertEqual(thermal['rowWords'],10);self.assertTrue(thermal['ownedBindings']);self.assertTrue(thermal['pure'])
   self.assertEqual(thermal['fields'],['temperature','energy','initialEnergy','appliedEnergy','environmentEnergy','importedEnergy','transferredEnergy','capacity','power','ambientTemperature'])
   self.assertEqual(s.snapshot(),saved);s.restore(saved);self.assertEqual(s.info()['contract'],contract)
   contract['bindingFamilies'].clear();self.assertEqual(len(s.info()['contract']['bindingFamilies']),24)
if __name__=='__main__':unittest.main()
