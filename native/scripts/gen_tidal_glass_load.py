#!/usr/bin/env python3
"""Generate the gallery's Tidal Glass load sequence as JSON lines and verify it natively.

The sequence mirrors native/web/template.html reset() and load() for the recipe
original-tidal-glass of native/examples/original_scenic_routes.py, then the
constructor commit() of ScenicOriginalSession (bindings/typescript/scenic_original.mjs).
Every command is applied to the built library and must be accepted; a rejection
raises and nothing is written. The default output is the committed fixture
tests/fixtures/tidal-glass-load.jsonl; --check compares instead of writing.
"""
from pathlib import Path
import argparse, json, sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'examples'))
sys.path.insert(0, str(ROOT / 'bindings/python'))
from original_scenic_routes import build_original_scenic_routes
from nocturne_native import NativeScene

FIXTURE = ROOT / 'tests/fixtures/tidal-glass-load.jsonl'
SEED = 2030


def encode(command):
    return json.dumps(command, ensure_ascii=False, allow_nan=False, separators=(',', ':'))


def load_sequence(library=None):
    """The accepted command sequence, in order, as dictionaries."""
    recipe = [r for r in build_original_scenic_routes() if r['id'] == 'original-tidal-glass'][0]
    if recipe['viewport'] != {'width': 160, 'height': 52}:
        raise ValueError('original-tidal-glass viewport changed: ' + json.dumps(recipe['viewport']))
    scene = NativeScene(seed=SEED, library=library)
    sequence = []

    def command(value):
        sequence.append(value)
        code = scene.command(value)
        if code not in (0, 1):
            raise ValueError('command not accepted: ' + encode(value))

    try:
        draft = scene.info()['prompt']['text']        # reset(commands, keepDraft=true) reads it first
        command({'op': 'reset', 'seed': SEED})
        for value in recipe['commands']:              # pearlCommands(recipe) is the identity for scenic recipes
            command(value)
        if draft:
            command({'op': 'draft', 'text': draft, 'emitWeather': False})
        viewport = recipe['viewport']                 # $('columns') and $('rows') come from recipe.viewport
        command({'op': 'resize', 'width': viewport['width'], 'height': viewport['height']})
        authored = [value for value in recipe['commands'] if value['op'] == 'prompt'][-1]
        if 'mode' in authored or 'alpha' in authored:
            raise ValueError('the authored prompt now sets mode or alpha; the UI defaults no longer apply')
        command({'op': 'prompt', 'alpha': 0.22, 'mode': 'marquee'})   # prompt-alpha 0.22, first prompt-mode option
        command({'op': 'accessibility', 'reducedMotion': False, 'screenReader': False})
        command({'op': 'pause', 'paused': False})    # running = !reducedMotion
        ms = scene.info()['clock']['timeUs'] // 1000  # ScenicOriginalSession.commit(): ScenicOriginalClock.sample
        command({'op': 'scene-art', 'timeMs': ms, 'controls': {'flow': 1, 'travel': (ms * (100 * .44704) / 1000) % 12000}})
    finally:
        scene.close()
    return sequence


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--library', type=Path, help='native library to verify against (default: native/dist)')
    parser.add_argument('--output', type=Path, default=FIXTURE)
    parser.add_argument('--check', action='store_true', help='compare with --output instead of writing it')
    args = parser.parse_args()
    text = ''.join(encode(value) + '\n' for value in load_sequence(args.library)).encode('utf-8')
    if args.check:
        if not args.output.is_file() or args.output.read_bytes() != text:
            print('DIFFERS:', args.output, file=sys.stderr)
            return 1
        print('MATCHES:', args.output, len(text.splitlines()), 'commands')
        return 0
    args.output.write_bytes(text)
    print('WROTE:', args.output, len(text.splitlines()), 'commands')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
