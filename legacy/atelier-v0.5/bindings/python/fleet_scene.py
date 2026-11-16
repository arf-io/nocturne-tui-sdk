"""Native renderer for a normalized Pearl Fleet scene, without its TypeScript host.

The application still owns focus, data ingestion and presentation. This module
only validates a scene envelope and delegates cells to the shared renderer.
"""
from studio import Studio,Node,Impulse

def renderFleetScene(scene:dict):
    """Return an owned native Frame from version-1 Fleet scene JSON data.

    Inputs: dictionary exported by FleetController.compose().
    Errors: TypeError/ValueError for malformed envelopes or native bounds.
    Example: frame = renderFleetScene(json.load(open('fleet.scene.json'))).
    Does not execute code, interpret terminal escapes, or fetch external content.
    """
    if not isinstance(scene,dict) or scene.get('version')!=1 or scene.get('kind')!='nocturne.fleet.scene':
        raise ValueError('Expected nocturne.fleet.scene version 1')
    cfg=scene['config']
    surface=Studio(**cfg['values'])
    surface.configure(**{k:cfg[k] for k in ('palette','starPalette','glyphs','novaGlyphs')})
    nodes=[Node(**n) for n in scene['nodes']]
    events=[Impulse(**e) for e in scene['events']]
    return surface.render(scene['timeMs'],nodes=nodes,events=events)
