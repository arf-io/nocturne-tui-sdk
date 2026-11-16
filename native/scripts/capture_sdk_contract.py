#!/usr/bin/env python3
"""Capture actual native contract discovery during combined qualification."""
from pathlib import Path
import argparse,json,sys,struct
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'bindings/python'))
from nocturne_native import NativeScene
from qualify import fingerprint
from sdk_contract import validateSDKContract,captureSDKArtifacts,validateSDKContractArtifacts
from delivery_runner import atomicJson
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 before=fingerprint()['sha256']
 artifacts=captureSDKArtifacts(ROOT.parent)
 with NativeScene(42) as scene:
  saved=scene.snapshot();contract=scene.info()['contract']
  for field,offset in [('abiVersion',8),('snapshotSchema',12),('sourceSchema',28)]:
   if contract[field]!=struct.unpack_from('<I',saved,offset)[0]:raise ValueError('Discovery/wire mismatch: '+field)
  if contract['snapshotCapacityBytes']!=len(saved) or scene.snapshot()!=saved:raise ValueError('Contract query changed source or capacity')
 after=fingerprint()['sha256']
 if before!=after:raise ValueError('Source changed during runtime contract capture')
 record={'schema':'nocturne.sdk-contract/v1','status':'PASS','runtime':'native C via Python',
  'sourceFingerprint':after,'contract':contract,'snapshotHeaderMatches':True,'queryPure':True,'artifacts':artifacts}
 release=json.loads((ROOT.parent/'RELEASE.json').read_text());validateSDKContract(record,release,after)
 validateSDKContractArtifacts(record,ROOT.parent)
 atomicJson(args.output,record)
if __name__=='__main__':main()
