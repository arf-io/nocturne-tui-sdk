"""Packaging must not accept stale or incomplete runtime discovery receipts."""
from pathlib import Path
import sys,unittest,copy,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from sdk_contract import REQUIRED_FEATURES,REQUIRED_BINDINGS,validateSDKContract,compareSDKContracts,captureSDKArtifacts,validateSDKContractArtifacts
class SDKContractReceipt(unittest.TestCase):
 def test_artifact_receipt_detects_replacement_missing_files_and_invalid_paths(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);dist=root/'native/dist';dist.mkdir(parents=True)
   for name in ('libnocturne_native.so','libnocturne_native.dylib','nocturne_native.wasm'):(dist/name).write_bytes(b'fixture '+name.encode())
   record=self.fixture();record['artifacts']=captureSDKArtifacts(root)
   self.assertEqual(validateSDKContractArtifacts(record,root),record['artifacts'])
   for name in ('native','wasm'):
    path=root/record['artifacts'][name]['path'];original=path.read_bytes()
    path.write_bytes(b'x'*len(original))
    with self.assertRaises(ValueError):validateSDKContractArtifacts(record,root)
    path.write_bytes(original);path.unlink()
    with self.assertRaises(ValueError):validateSDKContractArtifacts(record,root)
    path.write_bytes(original)
   for field,value in [('path','../outside'),('bytes',True),('sha256','not-a-hash')]:
    changed=copy.deepcopy(record);changed['artifacts']['wasm'][field]=value
    with self.assertRaises(ValueError):validateSDKContractArtifacts(changed,root)
   missing=copy.deepcopy(record);del missing['artifacts']['wasm']
   with self.assertRaises(ValueError):validateSDKContractArtifacts(missing,root)
 def fixture(self):
  return {'schema':'nocturne.sdk-contract/v1','status':'PASS','sourceFingerprint':'a'*64,
   'snapshotHeaderMatches':True,'queryPure':True,'contract':{'abiVersion':1,'snapshotSchema':0x20261032,
    'sourceSchema':0x20261032,'snapshotCapacityBytes':12499192,'metadataProfile':'nocturne.metadata/v1',
    'commandProfile':'nocturne.commands/v1','features':sorted(REQUIRED_FEATURES),'bindingFamilies':sorted(REQUIRED_BINDINGS)}}
 def test_completed_matching_receipt_preserves_exact_contract(self):
  record=self.fixture();before=copy.deepcopy(record)
  self.assertIs(validateSDKContract(record,{'abi':1,'snapshotSchema':'0x20261032'},'a'*64),record['contract'])
  self.assertEqual(record,before)
 def test_rebuilt_contract_must_match_packaged_discovery_exactly(self):
  packaged=self.fixture();rebuilt=copy.deepcopy(packaged);release={'abi':1,'snapshotSchema':'0x20261032'}
  self.assertEqual(compareSDKContracts(packaged,rebuilt,release,'a'*64),packaged['contract'])
  for field,value in [('snapshotCapacityBytes',12499193),('features',sorted(REQUIRED_FEATURES)+['future-feature']),
   ('bindingFamilies',sorted(REQUIRED_BINDINGS)+['future-family'])]:
   with self.subTest(field=field):
    changed=copy.deepcopy(rebuilt);changed['contract'][field]=value
    with self.assertRaises(ValueError):compareSDKContracts(packaged,changed,release,'a'*64)
 def test_incomplete_stale_mismatched_or_malformed_receipts_reject(self):
  changes=[('status','RUNNING'),('sourceFingerprint','b'*64),('snapshotHeaderMatches',False),('queryPure',False),
   ('abiVersion',2),('snapshotSchema',0x20261031),('sourceSchema',0x20261031),('snapshotCapacityBytes',True),
   ('metadataProfile','unknown'),('features',[]),('features',['typed-values','typed-values']),
   ('bindingFamilies',['widget','widget']),('bindingFamilies',[None]),('bindingFamilies',['widget'])]
  for field,value in changes:
   with self.subTest(field=field,value=value):
    record=self.fixture();target=record if field in ('status','sourceFingerprint','snapshotHeaderMatches','queryPure') else record['contract']
    target[field]=value
    with self.assertRaises(ValueError):validateSDKContract(record,{'abi':1,'snapshotSchema':'0x20261032'},'a'*64)
 def test_schema55_requires_resource_animation_and_selector_discovery(self):
  record=self.fixture();contract=record['contract']
  contract.update(snapshotSchema=0x20261055,sourceSchema=0x20261055,snapshotCapacityBytes=13548744)
  contract['features']+=['resource-animation-bindings','electrical-selectors']
  contract['bindingFamilies']+=['electrical-arc']
  release={'abi':1,'snapshotSchema':'0x20261055'}
  self.assertIs(validateSDKContract(record,release,'a'*64),contract)
  for field,name in [('features','resource-animation-bindings'),('features','electrical-selectors'),('bindingFamilies','electrical-arc')]:
   with self.subTest(field=field,name=name):
    missing=copy.deepcopy(record);missing['contract'][field].remove(name)
    with self.assertRaises(ValueError):validateSDKContract(missing,release,'a'*64)
if __name__=='__main__':unittest.main()
