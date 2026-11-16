"""Validate source-scoped runtime discovery before including it in an SDK."""
from pathlib import Path
import hashlib,re,sys
REQUIRED_FEATURES={'typed-values','host-payloads','character-rules','character-regions',
 'queued-transactions','panel-metadata','character-cell-inspection'}
REQUIRED_BINDINGS={'material','emitter','widget','camera','window','text','area','floor','state',
 'node','indicator','prompt','environment','field','flow','surface','surface-wave','float-body',
 'surface-foam','mesh','triangle','cell-art','accessibility'}
def validateSDKContract(record,release,sourceFingerprint):
 if not isinstance(record,dict) or record.get('schema')!='nocturne.sdk-contract/v1' or record.get('status')!='PASS':
  raise ValueError('Completed SDK runtime contract receipt required')
 if record.get('sourceFingerprint')!=sourceFingerprint:raise ValueError('SDK contract source fingerprint mismatch')
 if record.get('snapshotHeaderMatches') is not True or record.get('queryPure') is not True:
  raise ValueError('SDK contract capture checks incomplete')
 contract=record.get('contract')
 if not isinstance(contract,dict):raise ValueError('Runtime discovery object required')
 for field in ('abiVersion','snapshotSchema','sourceSchema','snapshotCapacityBytes'):
  if type(contract.get(field)) is not int or not 1<=contract[field]<=0xffffffff:raise ValueError('Invalid runtime contract '+field)
 if contract['abiVersion']!=release['abi'] or contract['snapshotSchema']!=int(release['snapshotSchema'],16):
  raise ValueError('Runtime ABI/schema disagrees with release declaration')
 if contract['sourceSchema']!=contract['snapshotSchema'] or contract['snapshotCapacityBytes']<24:
  raise ValueError('Runtime writer capacity or live schema invalid')
 if contract.get('metadataProfile')!='nocturne.metadata/v1' or contract.get('commandProfile')!='nocturne.commands/v1':
  raise ValueError('Unsupported SDK contract profile')
 for field in ('features','bindingFamilies'):
  values=contract.get(field)
  if not isinstance(values,list) or any(type(value) is not str or not value for value in values) or len(set(values))!=len(values):
   raise ValueError('Invalid runtime discovery '+field)
 if not REQUIRED_FEATURES.issubset(contract['features']):raise ValueError('Required SDK capabilities missing')
 if not REQUIRED_BINDINGS.issubset(contract['bindingFamilies']):raise ValueError('Required SDK binding families missing')
 if contract['snapshotSchema']>=0x20261055:
  if not {'resource-animation-bindings','electrical-selectors'}.issubset(contract['features']):
   raise ValueError('Required resource animation capabilities missing')
  if 'electrical-arc' not in contract['bindingFamilies']:
   raise ValueError('Required electrical binding family missing')
 return contract

def compareSDKContracts(packaged,rebuilt,release,sourceFingerprint):
 expected=validateSDKContract(packaged,release,sourceFingerprint)
 actual=validateSDKContract(rebuilt,release,sourceFingerprint)
 if actual!=expected:raise ValueError('Rebuilt runtime contract differs from SDK handoff')
 return actual

def artifactRecord(path,relative):
 path=Path(path)
 if path.is_symlink() or not path.is_file():raise ValueError('SDK binary missing or symlinked: '+relative)
 digest=hashlib.sha256()
 with path.open('rb') as stream:
  while block:=stream.read(1024*1024):digest.update(block)
 return {'path':relative,'bytes':path.stat().st_size,'sha256':digest.hexdigest()}

def captureSDKArtifacts(root):
 root=Path(root);native='native/dist/'+('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so')
 return {name:artifactRecord(root/relative,relative) for name,relative in [('native',native),('wasm','native/dist/nocturne_native.wasm')]}

def validateSDKContractArtifacts(record,root):
 artifacts=record.get('artifacts')
 if not isinstance(artifacts,dict) or set(artifacts)!={'native','wasm'}:raise ValueError('SDK native/WASM artifact bindings required')
 for name,entry in artifacts.items():
  allowed={'native/dist/libnocturne_native.so','native/dist/libnocturne_native.dylib'} if name=='native' else {'native/dist/nocturne_native.wasm'}
  if not isinstance(entry,dict) or entry.get('path') not in allowed or type(entry.get('bytes')) is not int or entry['bytes']<1 or not isinstance(entry.get('sha256'),str) or not re.fullmatch('[0-9a-f]{64}',entry['sha256']):
   raise ValueError('Malformed SDK artifact binding: '+name)
  actual=artifactRecord(Path(root)/entry['path'],entry['path'])
  if actual!=entry:raise ValueError('SDK contract binary mismatch: '+name)
 return artifacts
