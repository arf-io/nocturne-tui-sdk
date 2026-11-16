#!/usr/bin/env python3
"""Generate the recorded command streams of the transaction differential (native/docs/TRANSACTIONS.md).

Writes JSONL streams for native/tests/transaction_differential.c into an output directory (default
native/tests/fixtures/transactions/streams, which is not committed: the streams are a pure function of this script,
the committed corpus inputs and the seed, and regenerate byte for byte).

  recipes.jsonl     every native/recipes.json recipe
  gallery-NN.jsonl  the admitted Gallery entries (native/contract/GALLERY-ADMISSION.json via build_gallery's
                    admission and nullification), split into shards for parallel runs
  composite.jsonl   the three composite benchmark screens (fixtures/transactions/composite_scenes.py), 600 frames
  random.jsonl      seeded random hot-command storms on the composite screens and on a bare context
  targeted.jsonl    entries that drive each direct path's accept and rejection branches: literal sets of untyped,
                    typed, bound and readonly values; drags, wheels and camera inputs accumulated past nrValidState's
                    camera, flight and position bounds (rejected after the commit, then restored); control scalars in
                    draft, input and paste
  longrun.jsonl     every native/recipes.json recipe run to 30 s at 60 Hz with no other input, with {"frame":...}
                    checkpoints at 2 s and 30 s (the driver compares the snapshot and a fresh frame there)

Each entry is: {"entry":name}; a resize; the entry's own commands (rejectedCommands interleaved); then frames of
60 Hz `time` ticks with the entry's timed actions at their times, plus seeded hot commands (pointer, wheel, key,
paste, draft, input, select, set, widget and window updates, camera-input, pause) and seeded invalid commands:
out-of-range values, unknown keys, wrong types, malformed JSON, non-monotonic time, oversized paste, and batches
whose last child fails."""
import argparse, hashlib, json, os, random, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent
TICK = 16667


def dumps(command):
    return json.dumps(command, separators=(',', ':'), ensure_ascii=False)


def flatten(commands):
    for c in commands:
        if isinstance(c, dict):
            yield c
            if c.get('op') == 'batch':
                yield from flatten(c.get('commands', []))


class Inventory:
    """Identities the entry's own commands created, for addressing hot updates at live resources."""

    def __init__(self, commands):
        self.widgets, self.windows, self.values, self.texts, self.nodes = {}, set(), [], set(), set()
        self.cameraControls = False
        for c in flatten(commands):
            op = c.get('op')
            if op == 'widget' and 'id' in c:
                self.widgets.setdefault(c['id'], c.get('kind', self.widgets.get(c['id'], 'text')))
            elif op == 'window' and 'id' in c:
                self.windows.add(c['id'])
            elif op == 'define' and isinstance(c.get('path'), str):
                self.values.append((c['path'], c.get('type'), c.get('value')))
            elif op == 'text' and 'id' in c:
                self.texts.add(c['id'])
            elif op == 'node' and 'id' in c:
                self.nodes.add(c['id'])
            elif op == 'camera-controls':
                self.cameraControls = True


WORDS = ['frame', 'budget', 'copy', 'state', 'once', 'agent', 'render', 'prompt', 'glyph', 'weather', 'é', '漢字',
         '👩‍💻', 'á', 'tab\tstop', 'line\nbreak']
KEYS = ['a', 'b', 'x', 'Enter', 'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home',
        'End', 'Escape', 'Tab', 'i', 'h', 'l', 'w', 'd', 'u', 'p', '0', '$', 'F6', 'PageDown', 'PageUp', ' ']


def hot(rng, inv, width, height):
    """One seeded hot command against live resources."""
    k = rng.randrange(15)
    x, y = rng.randrange(-2, width + 2), rng.randrange(-2, height + 2)
    if k == 0:
        return {'op': 'pointer', 'phase': rng.choice(['down', 'move', 'move', 'up']), 'x': x, 'y': y,
                'button': rng.choice([0, 0, 1, 2]), 'shift': rng.random() < .2, 'alt': rng.random() < .1}
    if k == 1:
        return {'op': 'pointer', 'phase': 'move', 'x': x + rng.random(), 'y': y}
    if k == 2:
        return {'op': 'wheel', 'delta': rng.choice([-3, -1, 1, 2, 0.5]), 'x': x, 'y': y, 'shift': rng.random() < .2}
    if k == 3:
        command = {'op': 'key', 'key': rng.choice(KEYS)}
        for m in ('ctrl', 'shift', 'alt', 'meta'):
            if rng.random() < .08:
                command[m] = True
        return command
    if k == 4:
        return {'op': 'paste', 'text': ' '.join(rng.choice(WORDS) for _ in range(rng.randrange(1, 6)))}
    if k == 5:
        text = ' '.join(rng.choice(WORDS) for _ in range(rng.randrange(0, 8)))
        command = {'op': 'draft', 'text': text}
        if rng.random() < .5:
            command['emitWeather'] = rng.random() < .5
        if rng.random() < .3:
            command['caret'] = rng.randrange(0, len(text) + 1) if text else 0
        return command
    if k == 6:
        return {'op': 'input', 'text': rng.choice(WORDS)}
    if k == 7:
        return {'op': 'pause', 'paused': rng.random() < .3}
    if k == 8 and inv.widgets:
        wid = rng.choice(sorted(inv.widgets))
        kind = inv.widgets[wid]
        if kind in ('line', 'bars', 'sparkline', 'area', 'scatter', 'histogram', 'donut', 'pie', 'gauge'):
            return {'op': 'widget', 'id': wid, 'data': [round(rng.random(), 3) for _ in range(rng.randrange(1, 24))]}
        return {'op': 'widget', 'id': wid, 'text': ' '.join(rng.choice(WORDS) for _ in range(rng.randrange(0, 12)))}
    if k == 9 and inv.windows:
        return {'op': 'window', 'id': rng.choice(sorted(inv.windows)),
                'text': ' '.join(rng.choice(WORDS) for _ in range(rng.randrange(0, 20)))}
    if k == 10 and inv.values:
        path, kind, value = rng.choice(inv.values)
        if kind == 'boolean' or isinstance(value, bool):
            return {'op': 'set', 'path': path, 'value': rng.random() < .5}
        if kind == 'string' or isinstance(value, str):
            return {'op': 'set', 'path': path, 'value': rng.choice(WORDS)}
        return {'op': 'set', 'path': path, 'value': round(rng.uniform(-2, 2) if not isinstance(value, (int, float)) else value + rng.uniform(-1, 1), 3)}
    if k == 11:
        return {'op': 'camera-input', 'delta': [round(rng.uniform(-3, 3), 3), round(rng.uniform(-3, 3), 3), round(rng.uniform(-1, 1), 3)],
                'pan': rng.random() < .3}
    if k == 12:
        return {'op': 'select', 'anchor': rng.randrange(0, 4), 'caret': rng.randrange(0, 4)}
    if k == 13 and inv.nodes:
        return {'op': 'node', 'id': rng.choice(sorted(inv.nodes)), 'status': rng.choice(['ready', 'running', 'waiting'])}
    return {'op': 'pointer', 'phase': 'move', 'x': x, 'y': y}


def invalid(rng, inv, now):
    """One seeded command that today's engine rejects (or that probes a rejection boundary)."""
    k = rng.randrange(18)
    if k == 0:
        return {'op': 'pause', 'paused': 2}
    if k == 1:
        return {'op': 'time', 'timeUs': max(0, now - 50000)}
    if k == 2:
        return {'op': 'time', 'timeUs': now + TICK, 'budget': 0}
    if k == 3:
        return {'op': 'key', 'key': 'a', 'bogus': 1}
    if k == 4:
        return {'op': 'key'}
    if k == 5:
        return '{"op":"key","key":'
    if k == 6:
        return {'op': 'draft', 'text': 'abc', 'caret': 99}
    if k == 7:
        return {'op': 'paste', 'text': 'x' * rng.choice([5000, 20000])}
    if k == 8:
        return {'op': 'set', 'path': '/no/such/value', 'value': 1}
    if k == 9:
        return {'op': 'pointer', 'phase': 'sideways', 'x': 1, 'y': 1}
    if k == 10:
        return {'op': 'wheel', 'delta': 'up'}
    if k == 11:
        return {'op': 'camera-input', 'delta': [1e9, 0, 0]}
    if k == 12 and inv.widgets:
        return {'op': 'widget', 'id': rng.choice(sorted(inv.widgets)), 'alpha': 7}
    if k == 13:
        return {'op': 'batch', 'commands': [{'op': 'draft', 'text': 'rolled back'}, {'op': 'pause', 'paused': 3}]}
    if k == 14:
        return {'op': 'batch', 'commands': [{'op': 'key', 'key': 'z'}, {'op': 'time', 'timeUs': now}]}
    if k == 15 and inv.windows:
        return {'op': 'window', 'id': rng.choice(sorted(inv.windows)), 'x': 'left'}
    if k == 16:
        return {'op': 'input', 'text': 5}
    return {'op': 'time', 'timeUs': -1}


def entryStream(name, commands, actions=(), rejected=(), frames=120, width=160, height=48, hotRate=.5, badRate=.12,
                perFrame=None, seed=2030):
    rng = random.Random(int(hashlib.sha256((name + ':' + str(seed)).encode()).hexdigest()[:16], 16))
    inv = Inventory(commands)
    out = [{'entry': name}, {'op': 'resize', 'width': width, 'height': height}]
    for i, c in enumerate(commands):
        out.append(c)
        if rejected and i % max(1, len(commands) // (len(rejected) + 1)) == 0 and rejected:
            out.append(rejected[i % len(rejected)])
    out.extend(rejected)
    timed = sorted((a.get('timeUs', 0), k, a.get('command')) for k, a in enumerate(actions)
                   if isinstance(a, dict) and isinstance(a.get('command'), dict))
    last = max([t for t, _, _ in timed] + [0])
    total = max(frames, min(frames * 2, last // TICK + 30))
    pending = list(timed)
    for f in range(1, total + 1):
        now = f * TICK
        budget = rng.choice([None, None, None, 24, 2])
        tick = {'op': 'time', 'timeUs': now}
        if budget:
            tick['budget'] = budget
        out.append(tick)
        while pending and pending[0][0] <= now:
            out.append(pending.pop(0)[2])
        if perFrame:
            out.extend(perFrame(f - 1, now))
        while rng.random() < hotRate:
            out.append(hot(rng, inv, width, height))
        if rng.random() < badRate:
            out.append(invalid(rng, inv, now))
    return out


def targetedSet():
    out = [{'entry': 'targeted-set'}, {'op': 'resize', 'width': 160, 'height': 48},
           {'op': 'widget', 'id': 1, 'kind': 'progress', 'x': 2, 'y': 2, 'width': 30, 'height': 1},
           {'op': 'define', 'path': '/a', 'value': 1}, {'op': 'define', 'path': '/s', 'value': 'text'},
           {'op': 'define', 'path': '/r', 'value': 3, 'readonly': True},
           {'op': 'define', 'path': '/w', 'value': 0.5, 'binding': {'family': 'widget', 'id': 1, 'field': 'value'}}]
    for k in range(40):
        t = k * TICK
        out += [{'op': 'time', 'timeUs': t}, {'op': 'set', 'path': '/a', 'value': k * 1.5 - 20},
                {'op': 'set', 'path': '/a', 'value': [1e13, -1e13, 'x', True][k % 4]},
                {'op': 'set', 'path': '/s', 'value': 'v%d' % k}, {'op': 'set', 'path': '/r', 'value': k},
                {'op': 'set', 'path': '/w', 'value': (k % 10) / 10}, {'op': 'set', 'path': '/missing', 'value': 1},
                {'op': 'set', 'path': '/a', 'value': 1, 'expression': '1'}]
    return out


def targetedGestures():
    out = []
    warp = [scene for scene in compositeScenes() if scene[0] == 'warp'][0]
    for name, setup in (('targeted-gesture-flight', warp[2]), ('targeted-gesture-bare', [])):
        out += [{'entry': name}, {'op': 'resize', 'width': 160, 'height': 48}] + list(setup)
        x = 3
        for k in range(30):
            out += [{'op': 'time', 'timeUs': (k + 1) * TICK}, {'op': 'pointer', 'phase': 'down', 'x': 3, 'y': 3, 'button': 0}]
            for step in (40, 400, 4000, 40000, 400000):
                x += step if k % 2 == 0 else -step
                out.append({'op': 'pointer', 'phase': 'move', 'x': x, 'y': 3 + (k % 3)})
            out.append({'op': 'pointer', 'phase': 'up', 'x': x, 'y': 3})
            out.append({'op': 'pointer', 'phase': 'down', 'x': 5, 'y': 5, 'button': 2})
            out += [{'op': 'pointer', 'phase': 'move', 'x': 5 + 30000 * (j + 1), 'y': 5 - 9000 * (j + 1)} for j in range(4)]
            out.append({'op': 'pointer', 'phase': 'cancel', 'x': 5, 'y': 5})
            out += [{'op': 'wheel', 'delta': 100, 'x': 80, 'y': 10}, {'op': 'wheel', 'delta': -100, 'x': 80, 'y': 10, 'shift': True}]
    out += [{'entry': 'targeted-camera-input'}, {'op': 'resize', 'width': 160, 'height': 48},
            {'op': 'camera-input', 'delta': [1, 1, 1]}, {'op': 'camera-controls', 'rig': 'orbit'}]
    for k in range(60):
        out += [{'op': 'time', 'timeUs': (k + 1) * TICK},
                {'op': 'camera-input', 'delta': [99999, -99999, 99999], 'pan': k % 2 == 0},
                {'op': 'camera-input', 'delta': [3, 2, 1]}, {'op': 'wheel', 'delta': 100, 'x': 80, 'y': 10},
                {'op': 'wheel', 'delta': -100, 'x': 80, 'y': 10}]
        if k == 30:
            out.append({'op': 'camera-controls', 'rig': 'crane'})
    return out


def targetedGlyphs():
    out = [{'entry': 'targeted-glyphs'}, {'op': 'resize', 'width': 160, 'height': 48}] + prompt_commands()
    for k in range(20):
        out += [{'op': 'time', 'timeUs': (k + 1) * TICK}, {'op': 'draft', 'text': 'ok %d' % k},
                {'op': 'draft', 'text': 'bad\u0001%d' % k}, {'op': 'input', 'text': '\u0002'}, {'op': 'input', 'text': 'z'},
                {'op': 'paste', 'text': 'p\u0007q'}, {'op': 'paste', 'text': 'tab\tok'}, {'op': 'draft', 'text': '\u0000'},
                {'op': 'select', 'anchor': 0, 'caret': 1}, {'op': 'select', 'anchor': 0, 'caret': 999}]
    return out


def prompt_commands():
    return [{'op': 'prompt', 'active': True, 'mode': 'grow', 'minRows': 1, 'maxRows': 4}]


TARGETED = (targetedSet, targetedGestures, targetedGlyphs)


def admittedGallery():
    sys.path.insert(0, str(NATIVE / 'examples'))
    sys.path.insert(0, str(NATIVE / 'scripts'))
    from gallery_cases import build_cases
    import build_gallery
    library = json.loads((NATIVE / 'recipes.json').read_text()) + build_cases()
    return build_gallery.nullifiedRecipes(library)


def compositeScenes():
    sys.path.insert(0, str(HERE / 'fixtures' / 'transactions'))
    import composite_scenes
    return composite_scenes.SCENES


def recipeEntry(r, frames):
    view = r.get('viewport') or {}
    return entryStream(r['id'], r.get('commands', []), r.get('actions') or (), r.get('rejectedCommands') or (),
                       frames=frames, width=view.get('width', 160), height=view.get('height', 48))


def write(path, lines):
    with open(path, 'w', encoding='utf-8') as f:
        for line in lines:
            f.write((line if isinstance(line, str) else dumps(line)) + '\n')
    return len(lines)


def main():
    # The Gallery case builders iterate sets: fix the hash seed so the streams regenerate byte for byte.
    if os.environ.get('PYTHONHASHSEED') != '0':
        os.execve(sys.executable, [sys.executable] + sys.argv, dict(os.environ, PYTHONHASHSEED='0'))
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default=str(HERE / 'fixtures' / 'transactions' / 'streams'))
    parser.add_argument('--frames', type=int, default=120)
    parser.add_argument('--shards', type=int, default=8)
    parser.add_argument('--only', default='recipes,gallery,composite,random,longrun,targeted')
    args = parser.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    only = set(args.only.split(','))
    digest = {}
    if 'recipes' in only:
        recipes = json.loads((NATIVE / 'recipes.json').read_text())
        lines = [x for r in recipes for x in recipeEntry(r, args.frames)]
        digest['recipes.jsonl'] = (len(recipes), write(out / 'recipes.jsonl', lines))
    if 'gallery' in only:
        gallery = admittedGallery()
        for shard in range(args.shards):
            part = gallery[shard::args.shards]
            lines = [x for r in part for x in recipeEntry(r, args.frames)]
            digest['gallery-%02d.jsonl' % shard] = (len(part), write(out / ('gallery-%02d.jsonl' % shard), lines))
    if 'composite' in only:
        lines = []
        for name, _, setup, perFrame in compositeScenes():
            lines += entryStream('composite-' + name, setup, frames=600, perFrame=perFrame, hotRate=.25, badRate=.05)
        digest['composite.jsonl'] = (3, write(out / 'composite.jsonl', lines))
    if 'random' in only:
        lines = []
        for name, _, setup, perFrame in compositeScenes():
            for seed in range(4):
                lines += entryStream('random-%s-%d' % (name, seed), setup, frames=150, perFrame=perFrame, hotRate=.85,
                                     badRate=.4, seed=seed)
        for seed in range(4):
            lines += entryStream('random-bare-%d' % seed, [], frames=150, hotRate=.9, badRate=.4, seed=seed)
        digest['random.jsonl'] = (16, write(out / 'random.jsonl', lines))
    if 'targeted' in only:
        lines = [x for build in TARGETED for x in build()]
        digest['targeted.jsonl'] = (sum(1 for x in lines if isinstance(x, dict) and 'entry' in x), write(out / 'targeted.jsonl', lines))
    if 'longrun' in only:
        recipes = json.loads((NATIVE / 'recipes.json').read_text())
        lines = []
        for r in recipes:
            view = r.get('viewport') or {}
            lines += [{'entry': 'longrun-' + r['id']}, {'op': 'resize', 'width': view.get('width', 160), 'height': view.get('height', 48)}]
            lines += r.get('commands', [])
            for f in range(1, 1801):
                lines.append({'op': 'time', 'timeUs': f * TICK})
                if f in (120, 1800):
                    lines.append({'frame': f // 60})
        digest['longrun.jsonl'] = (len(recipes), write(out / 'longrun.jsonl', lines))
    for name, (count, n) in sorted(digest.items()):
        sha = hashlib.sha256((out / name).read_bytes()).hexdigest()
        print('%-18s %4d entries %7d lines sha256 %s' % (name, count, n, sha[:16]))


if __name__ == '__main__':
    main()
