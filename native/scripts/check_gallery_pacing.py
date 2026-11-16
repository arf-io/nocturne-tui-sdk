#!/usr/bin/env python3
"""Live gallery pacing in actual Chromium: bounded catch-up, frame rate and hidden-tab resume.

Runs the exact built gallery bytes (set_content, as check_browser.py does) at 1600x900.
Four attract scenes run live for 5 s each (20 s). An in-page sampler reads the native
clock once per second and a setter installed on window.nativeView, which every painted
frame assigns, counts frames; nothing depends on the page reporting on itself. A page that
also reports its own host backlog (nativeLab.pacing().backlogUs) is held to the same bounds.
Then two resumes on a live scene:
  visibility  document.hidden stubbed true, visibilitychange dispatched and
              requestAnimationFrame withheld for 5 s, as a hidden tab does; then restored,
              visibilitychange dispatched again and the withheld callbacks released;
  stall       the main thread is blocked for 5 s with no visibility event at all.
Thresholds are fixed here. The one value read from the page is its own frame budget, and only
up to a fixed maximum:
  catch-up (clock.targetUs - clock.timeUs) below 250 ms at every 1 s sample after the first
  2 s; the simulation keeps real time: in every scene the median native steps per second
  between samples, timed between the painted frames behind them, is at least 108 and at most
  132 (90 and 110 percent of the fixed 120 Hz step), so a simulation running ahead of the
  wall clock fails as surely as one that lags it; median painted frames per second over those
  samples above 30 in at least one of up to 3 passes over the scenes (every other assertion
  holds in every pass); after each resume the backlog is at most one frame budget at the first
  painted frames and the next sample; a hidden interval reaches the simulation by at most one
  frame budget beyond the wall time since it ended, and a stall by at most the 250 ms catch-up
  bound; after each resume the native clock advances at least 12 steps over the painted frames
  and the next sample, so a scene that resumes frozen fails. One frame budget is the one the
  page reports at that resume (nativeLab.pacing().frameBudgetUs: the recipe's frameBudget, else
  24 steps), believed only up to the fixed maximum of 24 steps at 120 Hz (200 ms): a larger
  report fails and the maximum still applies; a page that reports none is held to the earlier
  gallery default of 12 steps (100 ms).
The gallery's own error channel is read: tick() reports a live-loop exception to #error and
stops the simulation without raising a page error, so #error must be empty at the end of
every phase and no text may have been written to it at any time during the run. Writes are read
from the observer's mutation records (the nodes added and the values replaced), not from the box
when the observer fires, so a message written and cleared inside one task still counts.
Host contention is measured, not assumed: the 1-minute load average before and after each
pass. When the frame rate is the only failing assertion and every pass ran at a load of at
least 0.25 per logical CPU, the verdict is BLOCKED (frame rate not assessable on this host
now), never PASS; a simulation, catch-up, backlog or error-channel failure is FAIL at any load.
Exit 0 only when every assertion holds, 2 when any fails, 3 when BLOCKED: no browser can run,
or the frame rate alone failed under measured host contention.
Writes JSON to --output when given; nothing is written under native/evidence.
"""
from pathlib import Path
import argparse, hashlib, json, math, os, shutil, statistics

ROOT = Path(__file__).resolve().parents[1]
VIEWPORT = {'width': 1600, 'height': 900}
# Classic attract scenes (no `demonstrates`, so attract members by the documented rule), the
# same four the 2026-11-01 pacing investigation measured: particles with deposits (autumn),
# dense weather (rain), window compositing (windows) and text effects (text).
DEFAULT_SCENES = ('autumn', 'rain', 'windows', 'text')
SECONDS_PER_SCENE = 5
WARMUP_SAMPLES = 2            # the 1 s and 2 s samples of the run
CATCH_UP_LIMIT_US = 250_000
MIN_MEDIAN_FPS = 30.0
STEP_HZ = 120
# 90 percent of real time. With windows timed between paints, the fixed 24-step gallery measured
# per-scene medians of 119.2-120.5 at load 1.8-2.0 and 120.2 steps/s at 9 fps under 4x CDP CPU
# throttling. Below 5 painted frames per second one budget per frame cannot keep real time (8x
# throttling: 91 steps/s at 3.8 fps), and this assertion reports it. Earlier sample-timed windows
# on HEAD 9c497bb gave 112.9-126.7 at load 2.6-10. Review mutants: live-loop crash 0; one step per
# frame 17-47 steps/s, its frame rate.
MIN_STEPS_PER_SECOND = 108
# 110 percent of real time, the mirror of the floor: a simulation that runs ahead of the wall clock is as
# wrong as one that lags it. Double accrual (wanted = elapsedMs * 2000) ran at per-scene medians of 232-241
# steps/s and passed every other assertion in Chromium. A correct loop gains more than wall time only by
# draining a backlog it already holds, at most one frame budget (24 steps), and a window's paint times add
# jitter. A single window therefore tops out near 144 (141 measured at load 10-17 on 16 CPUs) while the
# per-scene median of four windows stays near 120: 119.4-119.7 on a quiet host (load 2.2), at most 124.9 at
# that heavy load, 127.3 in the 2026-11-02 independent re-review.
MAX_STEPS_PER_SECOND = 132
# Steps the clock must gain over the painted frames after a resume and the next sample: 100 ms
# of simulation, about half of real time across the shortest trace (12 frames at 60 Hz).
RESUME_MIN_STEPS = 12
FRAME_BUDGET_US = 12 * 1_000_000 // STEP_HZ   # a page that reports no frame budget: the earlier default, 12 steps = 100 ms
MAX_FRAME_BUDGET_US = 24 * 1_000_000 // STEP_HZ   # the largest frame budget a page's own report may set: 24 steps = 200 ms
HIDDEN_SECONDS = 5
TRACE_FRAMES = 12
# Frame rate is best of up to three passes over the scenes; a pass that reaches 30 fps ends it.
FPS_ATTEMPTS = 3
# A pass is contended when the 1-minute load average before or after it is at least this much
# per logical CPU (4.0 on the 16-CPU qualification host). HEAD 9c497bb measured 30.6-36.9 fps at
# load 2.6-4.6 and 19.5-25.3 fps at load 5.2-6.9 with every simulation assertion passing; the
# pre-fix gallery measured 16.7-17.8 fps at load 1.9-3.3, below the bound, which stays FAIL.
CONTENDED_LOAD_PER_CPU = 0.25
EXIT_CODES = {'PASS': 0, 'FAIL': 2, 'BLOCKED': 3}

INSTRUMENT = r"""()=>{
 if(window.__pacingCheck)return true;
 const P=window.__pacingCheck={paints:0,trace:null,traceLimit:0,samples:[],timer:0,t0:0,queued:[],realRaf:null,errors:[]};
 const host=()=>{try{return typeof nativeLab.pacing==='function'?nativeLab.pacing().backlogUs:null;}catch(error){return null;}};
 P.host=host;
 P.frameBudget=()=>{try{return typeof nativeLab.pacing==='function'?nativeLab.pacing().frameBudgetUs??null:null;}catch(error){return null;}};
 // The gallery's error channel: report() writes #error and act() clears it. A MutationObserver delivers its records
 // when the task that made the mutations ends, so reading the box then misses a message written and cleared inside
 // one task. The records are read instead: a node added to the box keeps its text after a later clear removes it, a
 // character data record keeps the value it replaced, and the last value written to an edited text node is read from it.
 const box=document.getElementById('error');
 P.errorText=()=>box?box.textContent:null;
 if(box){const note=text=>{if(text)P.errors.push({t:performance.now(),text:String(text).slice(0,400)});};
  new MutationObserver(records=>{const edited=new Set();
   for(const record of records){
    if(record.type==='childList')for(const node of record.addedNodes)note(node.textContent);
    else{note(record.oldValue);edited.add(record.target);}
   }
   for(const target of edited)note(target.data);
  }).observe(box,{childList:true,characterData:true,characterDataOldValue:true,subtree:true});
  note(box.textContent);}
 let view=window.nativeView;
 Object.defineProperty(window,'nativeView',{configurable:true,enumerable:true,get(){return view;},set(value){
  view=value;P.paints++;P.paintAt=performance.now();
  if(P.trace&&P.trace.length<P.traceLimit){const c=value.scene.info().clock;P.trace.push({t:performance.now(),timeUs:c.timeUs,targetUs:c.targetUs,step:c.step,host:host()});}
 }});
 P.start=scene=>{
  clearInterval(P.timer);P.samples=[];P.t0=performance.now();P.paints0=P.paints;P.scene=scene;
  P.timer=setInterval(()=>{const c=nativeLab.scene.info().clock,at=performance.now();P.samples.push({t:at-P.t0,at,paintAt:P.paintAt??null,paints:P.paints-P.paints0,timeUs:c.timeUs,targetUs:c.targetUs,step:c.step,paused:c.paused,host:host()});},1000);
 };
 P.stop=()=>{clearInterval(P.timer);return {scene:P.scene,samples:P.samples,error:P.errorText()};};
 return true;
}"""

LOAD = """id=>{const r=nativeLab.recipes.find(r=>r.id===id);if(!r)throw Error('Missing recipe '+id);
 nativeLab.hold();nativeLab.load(r);__pacingCheck.start(id);return nativeLab.demoRecipes.some(d=>d.id===id);}"""

HIDE = """()=>{const P=__pacingCheck;P.realRaf=window.requestAnimationFrame;P.queued=[];
 window.requestAnimationFrame=callback=>{P.queued.push(callback);return 0;};
 Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});
 Object.defineProperty(document,'visibilityState',{configurable:true,get:()=>'hidden'});
 document.dispatchEvent(new Event('visibilitychange'));
 const c=nativeLab.scene.info().clock;return {t:performance.now(),timeUs:c.timeUs,targetUs:c.targetUs,step:c.step,host:P.host(),frameBudgetUs:P.frameBudget()};}"""

SHOW = """frames=>{const P=__pacingCheck;delete document.hidden;delete document.visibilityState;
 P.trace=[];P.traceLimit=frames;const t=performance.now();
 document.dispatchEvent(new Event('visibilitychange'));
 window.requestAnimationFrame=P.realRaf;const queued=P.queued;P.queued=[];for(const callback of queued)P.realRaf.call(window,callback);
 return {t,hidden:document.hidden};}"""

STALL = """([frames,seconds])=>{const P=__pacingCheck,c=nativeLab.scene.info().clock,before={t:performance.now(),timeUs:c.timeUs,targetUs:c.targetUs,step:c.step,host:P.host(),frameBudgetUs:P.frameBudget()};
 P.trace=[];P.traceLimit=frames;const end=performance.now()+seconds*1000;while(performance.now()<end){}
 return {...before,end:performance.now()};}"""

TRACE = "()=>{const P=__pacingCheck,trace=P.trace;P.trace=null;return trace;}"


def backlog(row):
    """Largest backlog a sample shows: the core's catch-up and, when reported, the host's."""
    values = [row['targetUs'] - row['timeUs']]
    if isinstance(row.get('host'), (int, float)):
        values.append(row['host'])
    return max(values)


def frame_rates(samples):
    """Painted frames per second in each window between consecutive samples (first from the scene start)."""
    out, previous = [], {'t': 0.0, 'paints': 0}
    for row in samples:
        elapsed = (row['t'] - previous['t']) / 1000
        if elapsed > 0:
            out.append((row['paints'] - previous['paints']) / elapsed)
        previous = row
    return out


def step_rates(samples):
    """Native simulation steps per second between consecutive samples (120 keeps real time).

    The live clock moves only on painted frames, so a sample reads the step of the last paint
    before it. Each window is therefore timed between those paints (paintAt) when the page
    reports them; a window with no paint in it has no rate."""
    out = []
    for previous, row in zip(samples, samples[1:]):
        painted = all(isinstance(value.get('paintAt'), (int, float)) for value in (previous, row))
        elapsed = ((row['paintAt'] - previous['paintAt']) if painted else (row['t'] - previous['t'])) / 1000
        if elapsed > 0 and row['step'] >= previous['step']:
            out.append((row['step'] - previous['step']) / elapsed)
    return out


def passes(run):
    """The first pass over the scenes (run['scenes'], run['load']) and any retries after it."""
    return [{'scenes': run['scenes'], 'load': run.get('load')}, *run.get('retries', [])]


def summary(run):
    """Per-scene medians for the report; not assertions."""
    rows = []
    for index, attempt in enumerate(passes(run)):
        for scene in attempt['scenes']:
            fps, steps = frame_rates(scene['samples']), step_rates(scene['samples'])
            rows.append({'pass': index + 1, 'scene': scene['id'], 'medianFps': round(statistics.median(fps), 2) if fps else None,
                         'medianStepsPerSecond': round(statistics.median(steps), 1) if steps else None,
                         'maxCatchUpMs': round(max((backlog(row) for row in scene['samples']), default=0) / 1000, 1),
                         'load': attempt.get('load')})
    return rows


def counted_samples(scenes):
    """(scene, sample, fps of the window ending at it) after the pass's first WARMUP_SAMPLES samples."""
    flat = []
    for scene in scenes:
        for row, fps in zip(scene['samples'], frame_rates(scene['samples'])):
            flat.append((scene['id'], row, fps))
    return flat[WARMUP_SAMPLES:]


def pass_fps(scenes):
    rates = [fps for _, _, fps in counted_samples(scenes)]
    return statistics.median(rates) if rates else 0.0


def contended(load, cpus):
    """A pass is contended only when a load average was measured and reached the bound."""
    values = [value for value in (load or {}).values() if isinstance(value, (int, float))]
    return bool(values) and isinstance(cpus, int) and cpus > 0 and max(values) >= CONTENDED_LOAD_PER_CPU * cpus


def verdict(records):
    """FAIL when any assertion failed; BLOCKED when one could not be assessed; PASS only when all passed."""
    statuses = {row['status'] for row in records}
    return 'FAIL' if not records or 'FAIL' in statuses else 'BLOCKED' if 'BLOCKED' in statuses else 'PASS' if statuses == {'PASS'} else 'FAIL'


def evaluate(run):
    """Assertion records for one run; pure, so the thresholds can be tested without a browser."""
    records = []
    def record(name, ok, detail):
        status = ok if isinstance(ok, str) else 'PASS' if ok else 'FAIL'
        records.append({'name': name, 'status': status, 'detail': detail})
    attempts = passes(run)
    many = len(attempts) > 1
    label = lambda index: f'pass {index + 1}: ' if many else ''
    shapes = []
    for index, attempt in enumerate(attempts):
        scenes = attempt['scenes']
        observed = sum(scene['samples'][-1]['t'] / 1000 if scene['samples'] else 0 for scene in scenes)
        shapes.append((len(scenes) >= 4 and all(scene.get('attract') for scene in scenes) and observed >= 19.9,
                       label(index) + f"{len(scenes)} scenes ({', '.join(scene['id'] + ('' if scene.get('attract') else ' NOT ATTRACT') for scene in scenes)}), {observed:.1f} s observed"))
    record('at least four attract scenes for at least 20 s', all(ok for ok, _ in shapes), '; '.join(detail for _, detail in shapes))
    counted = [(index, *item) for index, attempt in enumerate(attempts) for item in counted_samples(attempt['scenes'])]
    worst = max(counted, key=lambda item: backlog(item[2]), default=None)
    record('catch-up below 250 ms at every 1 s sample after the first 2 s',
           all(counted_samples(attempt['scenes']) for attempt in attempts) and all(backlog(row) < CATCH_UP_LIMIT_US for _, _, row, _ in counted),
           'no samples' if worst is None else
           f"{len(counted)} samples; worst {backlog(worst[2]) / 1000:.1f} ms ({label(worst[0])}{worst[1]} at {worst[2]['t'] / 1000:.1f} s)")
    medians = [(index, scene['id'], statistics.median(step_rates(scene['samples'])) if step_rates(scene['samples']) else None)
               for index, attempt in enumerate(attempts) for scene in attempt['scenes']]
    per_scene = (', '.join(f"{label(index) if name == attempts[index]['scenes'][0]['id'] else ''}{name} {'no windows' if value is None else f'{value:.1f}'}"
                           for index, name, value in medians) + f' (real time {STEP_HZ})')
    record(f'simulation keeps real time: per-scene median at least {MIN_STEPS_PER_SECOND} steps/s',
           bool(medians) and all(value is not None and value >= MIN_STEPS_PER_SECOND for _, _, value in medians), per_scene)
    record(f'simulation keeps real time: per-scene median at most {MAX_STEPS_PER_SECOND} steps/s',
           bool(medians) and all(value is not None and value <= MAX_STEPS_PER_SECOND for _, _, value in medians), per_scene)
    cpus = run.get('cpuCount')
    rates = [pass_fps(attempt['scenes']) for attempt in attempts]
    best = max(range(len(attempts)), key=lambda index: rates[index])
    loaded = [contended(attempt.get('load'), cpus) for attempt in attempts]
    fps_ok = rates[best] > MIN_MEDIAN_FPS
    loads = lambda load: '-'.join(f'{value:.2f}' for value in (load or {}).values() if isinstance(value, (int, float))) or 'unmeasured'
    record(f'median frame rate above 30 fps in at least one of {FPS_ATTEMPTS} passes',
           'PASS' if fps_ok else 'BLOCKED' if all(loaded) else 'FAIL',
           '; '.join(f"pass {index + 1} median {rates[index]:.1f} fps at load {loads(attempt.get('load'))}{' (contended)' if loaded[index] else ''}"
                     for index, attempt in enumerate(attempts)) +
           f"; per scene in pass {best + 1} " +
           ', '.join(f"{scene['id']} {statistics.median(frame_rates(scene['samples'])) if scene['samples'] else 0:.1f}" for scene in attempts[best]['scenes']) +
           (f"; contended at load >= {CONTENDED_LOAD_PER_CPU * cpus:.1f} ({CONTENDED_LOAD_PER_CPU} x {cpus} CPUs)" if isinstance(cpus, int) else '; CPU count unknown'))
    for phase in ('visibility', 'stall'):
        resume = run.get(phase)
        if resume is None:
            record(f'{phase} resume measured', False, 'phase did not run')
            continue
        trace, after = resume['trace'], resume.get('after', [])
        rows = trace + after[:1]
        reported = resume['before'].get('frameBudgetUs')
        valid = isinstance(reported, (int, float)) and not isinstance(reported, bool) and math.isfinite(reported) and reported > 0
        budget = (FRAME_BUDGET_US if reported is None or not valid else min(reported, MAX_FRAME_BUDGET_US))
        record(f'{phase}: frame budget the page reports at most {MAX_FRAME_BUDGET_US // 1000} ms',
               reported is None or (valid and reported <= MAX_FRAME_BUDGET_US),
               f'not reported; the earlier gallery default of {FRAME_BUDGET_US / 1000:.0f} ms applies' if reported is None else
               f'page reports {reported!r} us; limit {budget / 1000:.1f} ms')
        worst = max((backlog(row) for row in rows), default=None)
        record(f'{phase}: backlog at most one frame budget after resume',
               bool(trace) and worst <= budget,
               'no painted frame after resume' if not trace else
               f"worst {worst / 1000:.1f} ms over {len(trace)} frames and {len(after[:1])} sample (limit {budget / 1000:.1f} ms)")
        if trace:
            first = trace[0]
            start = resume['shown'] if phase == 'visibility' else resume['before']['end']
            reached = first['timeUs'] - resume['before']['timeUs'] - (first['t'] - start) * 1000
            limit = budget if phase == 'visibility' else CATCH_UP_LIMIT_US
            record(f'{phase}: the {HIDDEN_SECONDS} s interval does not reach the simulation',
                   reached <= limit,
                   f"simulation advanced {(first['timeUs'] - resume['before']['timeUs']) / 1000:.1f} ms by the first frame, "
                   f"{reached / 1000:.1f} ms beyond wall time since resume (limit {limit / 1000:.0f} ms)")
        # Progress after resume, from the first painted frame to the latest frame or sample (the
        # sample may land before the first frame, so the largest step is taken, never the last).
        steps = [row['step'] for row in rows if isinstance(row.get('step'), (int, float))]
        gained = max(steps) - trace[0]['step'] if trace and len(steps) == len(rows) else None
        record(f'{phase}: the simulation advances at least {RESUME_MIN_STEPS} steps over the frames and sample after resume',
               gained is not None and gained >= RESUME_MIN_STEPS,
               'no painted frame after resume' if not trace else 'a frame or sample without a native step' if gained is None else
               f"{gained} steps from the first of {len(trace)} frames to the latest frame or sample "
               f"(steps {' '.join(str(row['step']) for row in trace)}; sample {' '.join(str(row['step']) for row in after[:1]) or 'none'}; "
               f"before resume {resume['before'].get('step', 'unread')})")
    record('no browser exceptions', not run.get('errors'), '; '.join(run.get('errors', []))[:400])
    # The gallery's own error channel. A phase whose #error was not read counts as a failure.
    phases = [(label(index) + scene['id'], scene.get('error')) for index, attempt in enumerate(attempts) for scene in attempt['scenes']]
    phases += [(phase, (run.get(phase) or {}).get('error')) for phase in ('visibility', 'stall')]
    unread = [name for name, text in phases if not isinstance(text, str)]
    shown = [f'{name}: {text[:120]}' for name, text in phases if isinstance(text, str) and text]
    written = run.get('errorChannel')
    problems = [f'{name}: not read' for name in unread] + shown
    if not isinstance(written, list):
        problems.append('error channel not observed')
    problems += [f"written at {row['t'] / 1000:.1f} s: {row['text'][:120]}" for row in (written or [])[:3]]
    record('gallery error channel (#error) empty at the end of every phase and never written',
           not problems, '; '.join(problems)[:400] or f'{len(phases)} phases read, nothing written')
    return records


def measure(page, scenes, seconds, attempts=FPS_ATTEMPTS):
    """Observe each scene live, then the two resumes; every value comes from the page's clock and hooks."""
    run = {'scenes': [], 'errors': [], 'cpuCount': os.cpu_count(), 'retries': []}
    page.evaluate(INSTRUMENT)
    def samples(count):
        page.wait_for_function('n=>__pacingCheck.samples.length>=n', arg=count, polling=100, timeout=(count + 60) * 1000)
    def observe():
        load = {'before': os.getloadavg()[0]}; out = []
        for scene in scenes:
            attract = page.evaluate(LOAD, scene); samples(seconds)
            stopped = page.evaluate('()=>__pacingCheck.stop()'); observed = stopped['samples'][:seconds]
            out.append({'id': scene, 'attract': attract, 'seconds': seconds, 'samples': observed, 'error': stopped['error']})
            print(f"observed {scene}: fps " + ' '.join(f'{fps:.1f}' for fps in frame_rates(observed)) +
                  ' | catch-up ms ' + ' '.join(f"{(row['targetUs'] - row['timeUs']) / 1000:.0f}" for row in observed) +
                  ' | steps/s ' + ' '.join(f'{rate:.0f}' for rate in step_rates(observed)), flush=True)
        load['after'] = os.getloadavg()[0]
        return {'scenes': out, 'load': load}
    first = observe(); run['scenes'], run['load'] = first['scenes'], first['load']
    while True:
        latest = passes(run)[-1]
        print(f"attempt {len(passes(run))} of up to {attempts}: median {pass_fps(latest['scenes']):.1f} fps at load "
              f"{latest['load']['before']:.2f} -> {latest['load']['after']:.2f} ({run['cpuCount']} CPUs)", flush=True)
        if pass_fps(latest['scenes']) > MIN_MEDIAN_FPS or len(passes(run)) >= attempts:
            break
        run['retries'].append(observe())
    # Hidden tab: a live scene, then 5 s with rAF withheld and document.hidden true.
    page.evaluate(LOAD, scenes[0]); samples(3)
    hidden = page.evaluate(HIDE); page.wait_for_timeout(HIDDEN_SECONDS * 1000)
    shown = page.evaluate(SHOW, TRACE_FRAMES); page.wait_for_timeout(1500)
    trace = page.evaluate(TRACE) or []; after = page.evaluate('()=>__pacingCheck.stop()')
    run['visibility'] = {'before': hidden, 'shown': shown['t'], 'trace': trace,
                         'after': [row for row in after['samples'] if row['at'] > shown['t']][:1], 'error': after['error']}
    # Stall: the main thread is blocked with no visibility event.
    page.evaluate(LOAD, scenes[0]); samples(3)
    before = page.evaluate(STALL, [TRACE_FRAMES, HIDDEN_SECONDS]); page.wait_for_timeout(1500)
    trace = page.evaluate(TRACE) or []; after = page.evaluate('()=>__pacingCheck.stop()')
    run['stall'] = {'before': before, 'trace': trace, 'after': [row for row in after['samples'] if row['at'] > before['end']][:1],
                    'error': after['error']}
    run['errorChannel'] = page.evaluate('()=>__pacingCheck.errors')
    for phase in ('visibility', 'stall'):
        resume = run[phase]
        print(f"{phase}: frames after resume {len(resume['trace'])}; backlog ms " +
              ' '.join(f'{backlog(row) / 1000:.0f}' for row in resume['trace'] + resume['after']) +
              ' | steps ' + ' '.join(str(row['step']) for row in resume['trace'] + resume['after']) +
              f" (before {resume['before']['step']})", flush=True)
    return run


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--gallery', type=Path, default=ROOT / 'Nocturne-Test-Harness.html')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--scenes', default=','.join(DEFAULT_SCENES))
    parser.add_argument('--seconds-per-scene', type=int, default=SECONDS_PER_SCENE)
    args = parser.parse_args(argv)
    scenes = [scene for scene in args.scenes.split(',') if scene]
    if len(scenes) < 4 or len(scenes) * args.seconds_per_scene < 20:
        parser.error('at least four scenes and 20 s in total')
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as error:
        print('BLOCKED Playwright unavailable:', error, flush=True)
        return 3
    errors = []
    with sync_playwright() as p:
        exe = os.environ.get('CHROMIUM') or shutil.which('chromium') or shutil.which('google-chrome')
        try:
            browser = p.chromium.launch(headless=True, executable_path=exe, args=['--no-sandbox'])
        except Exception as error:
            print('BLOCKED Chromium could not start:', str(error).splitlines()[0], flush=True)
            return 3
        page = browser.new_page(viewport=VIEWPORT, device_scale_factor=1, reduced_motion='no-preference')
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content(args.gallery.read_text()); page.wait_for_function('window.nativeLab !== undefined', timeout=120000)
        build = page.evaluate('nativeLab.scene.info().build')
        run = measure(page, scenes, args.seconds_per_scene)
        version = browser.version; browser.close()
    run['errors'] = errors
    records = evaluate(run)
    for row in records:
        print(row['status'], row['name'], '-', row['detail'], flush=True)
    status = verdict(records)
    passed = status == 'PASS'
    if status == 'BLOCKED':
        print('BLOCKED host contention: the frame rate is not assessable on this host now. Every pass ran at a load average '
              f'of at least {CONTENDED_LOAD_PER_CPU} per logical CPU and every simulation, catch-up, backlog and error-channel '
              'assertion passed; rerun on a quieter host. This is not a pass.', flush=True)
    result = {'scope': 'Exact gallery bytes via set_content in headless Chromium at 1600x900; live rAF pacing, '
                       'not physical display refresh, GPU presentation or Firefox.',
              'gallery': str(args.gallery), 'htmlSha256': hashlib.sha256(args.gallery.read_bytes()).hexdigest(),
              'build': build, 'browser': version, 'viewport': VIEWPORT, 'hostLoadAverage': list(os.getloadavg()),
              'thresholds': {'catchUpLimitUs': CATCH_UP_LIMIT_US, 'minMedianFps': MIN_MEDIAN_FPS,
                             'minStepsPerSecond': MIN_STEPS_PER_SECOND, 'maxStepsPerSecond': MAX_STEPS_PER_SECOND,
                             'resumeMinSteps': RESUME_MIN_STEPS,
                             'frameBudgetUs': FRAME_BUDGET_US, 'maxFrameBudgetUs': MAX_FRAME_BUDGET_US, 'warmupSamples': WARMUP_SAMPLES,
                             'hiddenSeconds': HIDDEN_SECONDS, 'fpsAttempts': FPS_ATTEMPTS,
                             'contendedLoadPerCpu': CONTENDED_LOAD_PER_CPU},
              'summary': summary(run), 'run': run, 'checks': records, 'status': status, 'passed': passed}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=1) + '\n')
    print(json.dumps({'checks': len(records), 'status': status, 'passed': passed,
                      'failures': [row['name'] for row in records if row['status'] == 'FAIL'],
                      'blocked': [row['name'] for row in records if row['status'] == 'BLOCKED']}, indent=1))
    return EXIT_CODES[status]


if __name__ == '__main__':
    raise SystemExit(main())
