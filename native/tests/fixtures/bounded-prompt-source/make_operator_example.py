"""Write operator-example.json, the operator's example for test_bounded_prompt_source.

Run: python3 make_operator_example.py. The Wave / tidepool preset sits in the bottom rows of an agent widget
window while scheduled updates scroll its text, over the flight-banked starfield.
"""
import json
from pathlib import Path
HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[2]
OUT = HERE / 'operator-example.json'
R = {r['id']: r for r in json.loads((NATIVE / 'recipes.json').read_text())}
P = {p['id']: p for p in json.loads((NATIVE / 'examples/first-prompt-original-presets.json').read_text())}
log = [
    'agent> reading the plan for the bounded prompt source',
    'agent> found nrFirstPromptPaint in first_prompt.c',
    'agent> the kernel owned the whole canvas; now a layer',
    'agent> region: cells, "prompt" or a widget rectangle',
    'agent> resolving the prompt frame every render',
    'agent> weather is clipped to the layer rectangle',
    'agent> ids are reset inside the layer only',
    'agent> header bar drawn around the layer on row 0',
    'agent> schema 0x20261098 appends a 48-byte record',
    'agent> older snapshots restore with no layer',
    'agent> alpha blends like widget fills and glyphs',
    'agent> a visible frame sits on the edge cells',
    'agent> z below and order wait for the layers design',
    'agent> recipe frames still match the base build',
    'agent> the region follows a growing prompt',
    'agent> tidepool sits under the agent text here',
    'agent> stars keep turning behind the window',
    'agent> four runtimes, one frame',
    'agent> writing the documentation example',
    'agent> waiting for review',
]
INNER = 12
def text(k):
    lines = log[:k]
    return '\n'.join(lines[-INNER:]) if lines else ''
widget = {'op': 'widget', 'id': 1, 'kind': 'text', 'x': 8, 'y': 6, 'width': 70, 'height': 16, 'border': 'rounded',
          'padding': 1, 'alpha': 0.35, 'text': text(4)}
t = P['tidepool']
source = {'op': 'prompt-source', 'values': t['values'], 'palette': [int(x.lstrip('#'), 16) for x in t['palette']],
          'layer': {'region': {'x': 9, 'y': 18, 'width': 68, 'height': 3}, 'z': 'above', 'order': 0, 'alpha': {'fg': 0.9, 'bg': 0.55}, 'frame': 'invisible'}}
# Text rows run from y+2 to y+23; the later log lines reach the bottom rows that the layer covers.
widget['text'] = text(4)
timeline = [{'timeUs': 400_000 * k, 'command': {'op': 'widget', 'id': 1, 'kind': 'text', 'text': text(4 + k)}} for k in range(1, len(log) - 3)]
commands = [c for c in R['flight-banked']['commands'] if c['op'] != 'status'] + [widget,
            {'op': 'draft', 'text': 'ask the agent', 'emitWeather': False}, source]
OUT.write_text(json.dumps({
    'description': "Operator example (2026-11-15): the Wave / tidepool prompt surface bound to the bottom rows of an agent widget window whose text scrolls over it, with its paper at alpha 0.55 and its glyphs at 0.9, over the oblique starfield in a coordinated turn. The layer region is an explicit cell rectangle inside the widget's border (the layer contract has no widget sub-rectangle).",
    'seed': 2030, 'width': 160, 'height': 48, 'timeUs': 8_000_000,
    'commands': commands, 'timeline': timeline}, indent=1) + '\n')
print(len(timeline))
