"""Window Theatre documents, poses, palettes and controls."""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'hosts/python'))
from atelier_application import rc2_window_commands


def build_rc2_window_studies():
    source = json.loads((ROOT / 'examples/rc2_window_presets.json').read_text())
    cases = []
    variants = [('windows', None), ('shapes', None)] + [('windows', e) for e in source['effects']]
    for scene_name, effect in variants:
        preset = source['scenes'][scene_name]
        for mode in ('isolated', 'application'):
            appearance = dict(preset['appearance'])
            if effect is not None:
                appearance['effect'] = effect
            camera = preset['camera']
            commands = [
                {'op':'resize', 'width':preset['width'], 'height':preset['height']},
                {'op':'environment', 'presentation':'canvas', 'style':'solid',
                 'background':int(preset['palette']['background'][1:], 16), 'stars':0},
                {'op':'floor', 'enabled':False, 'visible':False},
                {'op':'prompt', 'active':mode == 'application', 'mode':'marquee', 'alpha':.3},
                {'op':'camera', 'position':[camera['x'],camera['y'],-camera['z']],
                 **{k:camera[k] for k in ('yaw','pitch','roll','near','far','fov')}, 'orthographic':False, **({'profile':'original'} if mode == 'application' else {})},
            ]
            for index, item in enumerate(preset['windows']):
                commands.extend(rc2_window_commands(
                    item, source_index=index, native_id=index+1,
                    palette=preset['palette'], options=preset['options'],
                    appearance=appearance, waveform=preset['waveform']))
            # Creating a native window selects it. A metadata-only edit restores
            # the selected window without changing its visibility.
            selected = next(i+1 for i,w in enumerate(preset['windows']) if w['id'] == preset['selected'])
            commands.append({'op':'window','id':selected})
            if mode == 'application':
                commands.append({'op':'window-application','paletteWindowId':1,'scene':scene_name})
                commands.append({'op':'draft','text':'','emitWeather':False})
            name = 'Window Theatre' if scene_name == 'windows' else 'Shapes / beyond the rectangle'
            suffix = scene_name
            actions = []
            if effect is not None:
                name = 'Window Theatre / ' + effect
                suffix = 'window-' + effect
                actions = [
                    {'timeUs':1000000, 'command':{'op':'window-action','id':1,'action':'minimize','durationMs':appearance['durationMs']}},
                    {'timeUs':3000000, 'command':{'op':'window-action','id':1,'action':'restore','durationMs':appearance['durationMs']}},
                ]
            case = {
                'id':f'rc2-{suffix}-{mode}', 'name':f'{name} / {mode}',
                'subtitle':'Pearl, Atlas and Iris: documents, palette, poses and window controls.',
                'mode':mode, 'originalScene':scene_name,
                'demonstrates':{'feature':'rc2-window-compositions'},
                'provenance':{'release':source['source']['release'], 'component':name,
                              'htmlSha256':source['source']['htmlSha256']},
                'demo':effect is None and mode == 'application',
                'viewport':{'width':preset['width'],'height':preset['height']},
                'commands':commands, 'actions':actions, 'autoActions':bool(actions),
                'sampleTimesUs':[1425000,3425000] if effect else [0,425000,1700000],
                'interactionInstructions':'Select Pearl, Atlas or Iris in Window controls. Minimize, restore or open its full document. Middle-drag to orbit the picked point; right-drag to pan.',
            }
            if effect is not None:
                case['originalEffect'] = effect
            cases.append(case)
    return copy.deepcopy(cases)
