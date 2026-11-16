"""Current output contract expectations; never rewrites historical fixture input."""
from functools import lru_cache
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'bindings/python'))
from nocturne_native import NativeScene

@lru_cache(maxsize=1)
def current_schema():
    with NativeScene() as scene:
        contract=scene.info_complete()['contract']
        assert contract['abiVersion']==1 and contract['snapshotSchema']>0
        return contract['snapshotSchema']

def snapshot_size(scene):
    size=int(scene._lib.nrSnapshotSizeFor(scene._context))
    assert size>=24 and size==scene.info_complete()['contract']['snapshotCapacityBytes']
    return size
