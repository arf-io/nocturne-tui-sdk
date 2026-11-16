// Generate native/tests/fixtures/scenic-route-ticks.jsonl: for each route of build_original_scenic_routes()
// (native/examples/original_scenic_routes.py), the gallery's load of that route, then 300 live ticks, each a
// {op:'time',timeUs,budget:24} and the scene-art sample of the gallery's own clock, ScenicOriginalClock
// (native/bindings/typescript/scenic_original.mjs), at the live cadence of 16,667 us per tick.
//
// The load mirrors native/web/template.html load() and reset(): reset with the gallery seed 2030, the route's
// commands, resize to its viewport, the prompt UI defaults (alpha 0.22, mode marquee), accessibility with both
// flags false and pause false, then ScenicOriginalSession's constructor commit, the clock's sample at time 0.
// A tick's sample time is floor(timeUs / 1000), the time ScenicOriginalSession.commit() reads back after an
// accepted time command that stays inside its budget, as every tick here does.
//
// Usage: node native/scripts/gen_scenic_route_ticks.mjs > native/tests/fixtures/scenic-route-ticks.jsonl
// It reads the routes through the Python interpreter named by PYTHON (else python3); it writes only stdout.
// test_command_path_lint.py (T1(n)) compares the committed fixture with this output byte for byte.
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {ScenicOriginalClock} from '../bindings/typescript/scenic_original.mjs';

const NATIVE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SEED = 2030, TICKS = 300, TICK_US = 16667, BUDGET = 24;
const python = process.env.PYTHON || 'python3';
const read = 'import json,sys;sys.path.insert(0,sys.argv[1]);from original_scenic_routes import build_original_scenic_routes;print(json.dumps(build_original_scenic_routes()))';
const routes = JSON.parse(execFileSync(python, ['-I', '-c', read, path.join(NATIVE, 'examples')], {encoding: 'utf8'}));
if (routes.length !== 4) throw new Error(`expected the four original scenic routes, found ${routes.length}`);
const lines = [];
for (const route of routes) {
  const authored = route.commands.filter(command => command.op === 'prompt').at(-1);
  if (authored && ('mode' in authored || 'alpha' in authored)) throw new Error(`${route.id}: the authored prompt sets mode or alpha; the UI defaults no longer apply`);
  lines.push({route: route.id, scene: route.originalScenic, ticks: TICKS, tickUs: TICK_US, budget: BUDGET});
  lines.push({op: 'reset', seed: SEED});
  for (const command of route.commands) lines.push(command);
  lines.push({op: 'resize', width: route.viewport.width, height: route.viewport.height});
  lines.push({op: 'prompt', alpha: 0.22, mode: 'marquee'});
  lines.push({op: 'accessibility', reducedMotion: false, screenReader: false});
  lines.push({op: 'pause', paused: false});
  const clock = new ScenicOriginalClock(route.originalScenic);
  lines.push(clock.sample(0));
  for (let tick = 1; tick <= TICKS; tick++) {
    const timeUs = tick * TICK_US;
    lines.push({op: 'time', timeUs, budget: BUDGET});
    lines.push(clock.sample(Math.floor(timeUs / 1000)));
  }
}
process.stdout.write(lines.map(line => JSON.stringify(line)).join('\n') + '\n');
