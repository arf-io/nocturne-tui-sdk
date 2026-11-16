"""Record the base-build oracles for test_bounded_prompt_source.

Run once against the library built from the commit before bounded prompt sources existed:

    python3 capture_base.py <path to that build's libnocturne_native> <source commit>

It writes frames.json and schema97/ beside this file. Every value comes from executing that library;
nothing is computed or edited by hand.
"""
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[2]
sys.path.insert(0, str(NATIVE / 'bindings/python'))
from nocturne_native import NativeScene  # noqa: E402

SCENE = json.loads((HERE / 'scene.json').read_text())
RECIPES = {r['id']: r for r in json.loads((NATIVE / 'recipes.json').read_text())}
PRESETS = [p for p in json.loads((NATIVE / 'examples/first-prompt-original-presets.json').read_text())
           if p['values']['layout'] == 1]
TIMES = (2_000_000, 30_000_000)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run_all(scene, commands):
    for command in commands:
        while scene.command(command) == 1:
            pass


def preset_command(preset):
    """The preset as one prompt-source command (colours as RGB integers)."""
    command = {'op': 'prompt-source', 'values': preset['values']}
    for key in ('palette', 'starPalette', 'glyphs'):
        if key in preset:
            command[key] = [int(x.lstrip('#'), 16) if isinstance(x, str) else x for x in preset[key]]
    return command


def composite(library, extra, time_us):
    """The composite scene: oblique starfield in a coordinated turn, a widget, an agent window, a growing
    prompt with typing weather. Text is typed shortly before the frame so weather is in flight."""
    scene = NativeScene(seed=SCENE['seed'], library=library)
    run_all(scene, SCENE['commands'])
    run_all(scene, extra)
    scene.advance_to(time_us - SCENE['typeBeforeUs'])
    run_all(scene, [{'op': 'input', 'text': SCENE['typed']}])
    scene.advance_to(time_us)
    return scene


def main(library, commit):
    frames = {}
    for recipe_id, recipe in RECIPES.items():
        for time_us in TIMES:
            with NativeScene(seed=2030, library=library) as scene:
                scene.command({'op': 'resize', 'width': 160, 'height': 48})
                run_all(scene, recipe['commands'])
                scene.advance_to(time_us)
                frames[f'{recipe_id}@{time_us}'] = digest(scene.render().bytes)
    full = {}
    for time_us in TIMES:
        with composite(library, [], time_us) as scene:
            full[f'none@{time_us}'] = digest(scene.render().bytes)
        for preset in PRESETS:
            with composite(library, [preset_command(preset)], time_us) as scene:
                full[f"{preset['id']}@{time_us}"] = digest(scene.render().bytes)
    (HERE / 'frames.json').write_text(json.dumps({
        'method': 'NativeScene(seed=2030); resize 160x48; recipe commands from native/recipes.json (pending loop); '
                  'advance_to(timeUs); sha256 of render().bytes. composite: scene.json commands, then the preset as '
                  'one prompt-source command (none = without), advance_to(timeUs - typeBeforeUs), input typed, '
                  'advance_to(timeUs).',
        'sourceCommit': commit,
        'runtimeSha256': digest(Path(library).read_bytes()),
        'recipes': frames,
        'composite': full,
    }, indent=1, sort_keys=True) + '\n')
    tidepool = next(p for p in PRESETS if p['id'] == 'tidepool')
    with composite(library, [preset_command(tidepool)], TIMES[0]) as scene:
        snapshot, frame = scene.snapshot(), scene.render().bytes
        info = scene.info()['prompt']
    schema = struct.unpack_from('<I', snapshot, 12)[0]
    out = HERE / f'schema{schema & 0xff:02x}'
    out.mkdir(exist_ok=True)
    (out / 'snapshot.gz').write_bytes(gzip.compress(snapshot, mtime=0))
    (out / 'frame.gz').write_bytes(gzip.compress(frame, mtime=0))
    (out / 'manifest.json').write_text(json.dumps({
        'schema': f'0x{schema:08x}', 'sourceCommit': commit, 'runtimeSha256': digest(Path(library).read_bytes()),
        'snapshotSha256': digest(snapshot), 'frameSha256': digest(frame), 'scene': 'composite + tidepool (full viewport)',
        'timeUs': TIMES[0], 'promptText': info['text'], 'weatherEvents': info['appearance']['weather']['eventCount'],
        'actualRuntimeExecution': True,
    }, indent=2) + '\n')
    print(len(frames), 'recipe frames;', len(full), 'composite frames; snapshot schema', hex(schema))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
