#!/usr/bin/env python3
"""Execute the native acceptance plan to completion, not a fixed polling window.

Each invocation creates its own receipt/log directory. A PASS is written only after
all required subprocesses have exited and the source fingerprint is unchanged.
An absent runtime is BLOCKED, never skipped into a four-runtime pass.
"""
from __future__ import annotations
from pathlib import Path
from contextlib import ExitStack
import argparse, hashlib, json, math, os, platform, re, shutil, signal, socket, subprocess, sys, time
from delivery_runner import RunJournal, atomicJson
from original_c_oracles import originalOracleInputs, originalOracleJobs
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'tools/qualification'))
from checkpoints import CheckpointStore, bindingDigest, fileDigest


def fingerprint(root: Path = ROOT):
    """Hash current native source and qualification code using relative names."""
    files={}
    for folder in ['src','include','freestanding','bindings','scripts','tests','hosts','examples','docs','unicode']:
        for p in sorted((root/folder).rglob('*')):
            if not p.is_file() or any(x in {'target','__pycache__','node_modules'} for x in p.relative_to(root).parts): continue
            files[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    for name in ['web/template.html','web/workshop_fields.json','web/workshop_help.json','recipes.json','palettes.json','catalogue.json','port-ledger.json','CAPABILITY-STATUS.json','IMPLEMENTATION-COVERAGE.json','SOURCE-PROVENANCE.json','build.sh','run.sh',
                 'contract/NULLIFICATION.json','contract/NULLIFICATION.schema.json','contract/GALLERY-ADMISSION.json']:
        p=root/name
        if p.is_file(): files[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    rootNames=['README.md','DESIGN.md','UX-CONTRACT.md','LLM-HANDOFF.md','AGENTS.md','RELEASE.json','BUILD-IDENTITY.json',
               'tools/requirements-qualification.txt','publish-private.sh','build-native.sh','run-native.sh','run-framework.sh',
               'qualify-native.sh','native-env.sh','.github/workflows/nocturne.yml','.github/workflows/rc4-native.yml','.forgejo/workflows/nocturne.yml']
    rootNames.extend(p.name for p in sorted(root.parent.glob('CHANGELOG*.md')))
    for name in rootNames:
        p=root.parent/name
        if p.is_file(): files['../'+name]=hashlib.sha256(p.read_bytes()).hexdigest()
    for folder in ['src','include','integrations','tools/release','tools/qualification','tools/ci','docs/rc4-completion',
                   'docs/rc4-contracts4','docs/rc4-contracts5','docs/rc4-contracts6','docs/rc4-contracts7','docs/current']:
        for p in sorted((root.parent/folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:
                files['../'+p.relative_to(root.parent).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    for p in originalOracleInputs(root):
        if p.is_file():files[p.relative_to(root).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
    return {'sha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'files':files}


def qualificationEnvironment(environment, root: Path = ROOT.parent) -> dict:
    """Copy of ``environment`` with the repository root first on PYTHONPATH.

    Test modules import ``native.*``; every step's interpreter must resolve it
    against this checkout whatever the caller exported. Caller entries are kept,
    byte for byte, after the root; applying the function twice changes nothing.
    """
    result=dict(environment);existing=result.get('PYTHONPATH','');first=str(root)
    if existing.split(os.pathsep)[0]!=first: result['PYTHONPATH']=first+(os.pathsep+existing if existing else '')
    return result


def toolExecutables(tool: dict, environment: dict) -> dict:
    """Bind resolved real tool bytes, including absence; never install tools.

    Version text alone cannot distinguish a replaced executable. Symlinks resolve
    to the exact binary/script hashed here. This is not a hermetic OS/shared-library
    closure or a qualification of unexecuted physical devices.
    """
    names={'python':sys.executable, 'cc':tool.get('cc') or 'cc',
           'clang':tool.get('wasmCC') or 'clang', 'wasm-ld':tool.get('wasmLD') or 'wasm-ld',
           'cxx':environment.get('CXX') or 'c++', 'node':'node', 'go':'go',
           'rustc':'rustc', 'cargo':'cargo', 'typescript':'tsc',
           'chromium':environment.get('CHROMIUM') or 'chromium', 'ffmpeg':'ffmpeg', 'ffprobe':'ffprobe'}
    result={}
    for name, command in names.items():
        found=shutil.which(command,path=environment.get('PATH'))
        if found:
            path=Path(found).resolve()
            result[name]={'command':command,'path':str(path),'sha256':fileDigest(path)}
        else:
            result[name]={'command':command,'status':'BLOCKED','reason':'Executable unavailable'}
    # Environment paths alone do not bind mutable external font/library bytes.
    # These are caller-owned qualification inputs and never SDK payloads.
    for variable in ['NOCTURNE_HARFBUZZ_LIBRARY','NOCTURNE_SHAPING_FONT'] + (['NOCTURNE_OTF_FONT'] if environment.get('NOCTURNE_OTF_FONT') else []):
        value=environment.get(variable)
        path=Path(value).resolve() if value else None
        if path and path.is_file():
            result[variable]={'path':str(path),'sha256':fileDigest(path)}
        else:result[variable]={'status':'BLOCKED','reason':'Explicit external presentation fixture unavailable'}
    return result


def discoveredCaseId(kind: str, relative: str) -> str:
    """Stable safe checkpoint name; preserve readable stem and exact path identity."""
    path=Path(relative)
    if not re.fullmatch('[A-Za-z0-9_-]+',kind) or path.is_absolute() or '..' in path.parts:
        raise ValueError('Unsafe discovered case kind/path')
    stem=re.sub('[^A-Za-z0-9_-]','_',path.stem)[:64]
    return 'discovered-'+kind+'-'+stem+'-'+hashlib.sha256(relative.encode('utf-8')).hexdigest()


def sanitizerRunEnvironment(platformName: str | None = None) -> dict[str, str]:
    """Declared runtime options for plan programs built with AddressSanitizer.

    LeakSanitizer is part of the sanitizer gate where its runtime exists. Linux
    enables it by default, but an inherited ASAN_OPTIONS or LSAN_OPTIONS such as
    detect_leaks=0 or exitcode=0 would silently remove it, so both variables are
    replaced for those cases. Apple's ASan runtime does not run LeakSanitizer;
    other platforms keep the toolchain default, which is not a declared leak
    gate (native/docs/BUILD-SCOPE.md).
    """
    name = sys.platform if platformName is None else platformName
    return {'ASAN_OPTIONS':'detect_leaks=1','LSAN_OPTIONS':'detect_leaks=1'} if name.startswith('linux') else {}


def addressSanitizedOutputs(plan: list) -> set[str]:
    """Normalized paths written by plan compiler commands that enable AddressSanitizer."""
    outputs = set()
    for step in plan:
        argv = [str(arg) for arg in step[1]]
        sanitizers = {name for arg in argv if arg.startswith('-fsanitize=') for name in arg.split('=', 1)[1].split(',')}
        if 'address' in sanitizers and '-o' in argv[:-1]:
            outputs.add(os.path.normpath(ROOT/(step[2] if len(step) > 2 else '')/argv[argv.index('-o')+1]))
    return outputs


# Deadline floors, in seconds, for cases that outlast the default --step-timeout. The flag raises a
# floor and never lowers it, so the 7200 s CI budget still applies to every case. fingerprint-stability
# replays qualification cases in a scratch replica of the checkout: about 744 s as measured in the
# review of the generated-outputs repair (native/docs/BUILD-SCOPE.md).
STEP_TIMEOUT_FLOORS={'fingerprint-stability':1800}
# Declared environment pins, merged into a case's environmentOverrides as the sanitizer cases' leak options
# are: they replace what the caller exported, are bound into the checkpoint plan and are recorded on the step.
# fingerprint-stability runs its default replay when the selection is empty, so an exported
# NOCTURNE_FINGERPRINT_STABILITY_STEPS can narrow a run of the module by hand but never the journalled step,
# and a PASS recorded for the step means every default case was replayed (native/docs/BUILD-SCOPE.md).
STEP_ENVIRONMENT_PINS={'fingerprint-stability':{'NOCTURNE_FINGERPRINT_STABILITY_STEPS':''}}


def buildSwitchesProblem(record, strict: bool):
    """Why a strict receipt must FAIL on the build step's dist/build-switches.json (build_switches.py), or None."""
    if not strict:
        return None
    if record is None:
        return 'build-switch record missing (dist/build-switches.json)'
    if not isinstance(record, dict) or record.get('schema') != 'nocturne.native.build-switches.v1':
        return 'build-switch record has an unknown schema'
    if record.get('NOCTURNE_SHADOW_CHECK') is not None:
        return 'build-switch record names NOCTURNE_SHADOW_CHECK=' + str(record['NOCTURNE_SHADOW_CHECK']) + ': a shadow-check build cannot qualify'
    return None

def checkpointPlan(plan: list, timeoutSeconds: float) -> list[dict]:
    """Describe every strict command, its deadline, its declared environment overrides and the generated evidence it must retain."""
    evidence=ROOT/'evidence'
    outputs={
        'build':[ROOT/'dist'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so'), ROOT/'dist/nocturne_native.wasm', ROOT/'dist/build-switches.json'],
        'gallery':[ROOT/'Nocturne-RC4-Source-Build.html',ROOT.parent/'Nocturne-RC4.html'],
        'workshop-browser':[evidence/'workshop-browser/RESULTS.json',evidence/'workshop-browser/workshop-narrow.png',evidence/'workshop-browser/composition.json'],
        'area-geometry-browser':[evidence/'area-geometry-browser.json'],
        'prompt-presentation-browser':[evidence/'prompt-presentation-browser.json'],
        'bidi-prompt-browser':[evidence/'bidi-prompt-browser.json'],
        'source-optics-browser':[evidence/'source-optics-browser.json'],
        'soft-fronts-browser':[evidence/'soft-fronts-browser.json'],
        'color-fields-browser':[evidence/'color-fields-browser.json'],
        'gallery-studies':[evidence/'gallery-studies.json',evidence/'gallery-study-cases.json'],
        'gallery-studies-wasm':[evidence/'gallery-studies-wasm.json'],
        'parity':[evidence/'parity.json',evidence/'plan.ndjson'],
        'sdk-contract':[evidence/'SDK-CONTRACT.json'],
        'unicode-conformance':[evidence/'unicode-conformance'/name for name in
            ['RESULTS.json','cases.ndjson','cases.rust.txt','python.jsonl','typescript.jsonl',
             'go.jsonl','rust.jsonl','bidi-characters.json','bidi-classes.json','bidi-wasm.json','python.stderr','typescript.stderr','go.stderr','rust.stderr',
             'go-build.log','rust-build.log']],
        'source-examples':[evidence/'examples.json'],
        'graph-weather-browser':[evidence/'graph-weather-browser.json'],
        'retained-treatment-browser':[evidence/'retained-treatment-browser.json'],
        'controller-workflow-browser':[evidence/'controller-workflow-browser.json'],
        'emitter-control-browser':[evidence/'emitter-control-browser.json'],
        'cleanup-workflow-browser':[evidence/'cleanup-workflow-browser.json'],
        'fluid-lifecycle-browser':[evidence/'fluid-lifecycle-browser.json'],
        'state-workflow-browser':[evidence/'state-workflow-browser.json'],
        'status-workflow-browser':[evidence/'status-workflow-browser.json'],
        'input-workflow-browser':[evidence/'input-workflow-browser.json'],
        'font-document-view':[evidence/'font-document-view'/name for name in ['browser.json','gallery.html','examples.json']],
        'font-presentation':[evidence/'font-presentation'/name for name in ['RESULTS.json','screen.svg','example-0.stdout','example-0.stderr','example-1.stdout','example-1.stderr']],
        'graph-consumers':[evidence/'graph-consumer.json',evidence/'graph-consumer-runs'],
        'field-equation-error':[evidence/'field-lookup-error.json'],
        'sanitizer-build':[ROOT/'dist/native-safety'],
        'source-model-sanitizer-build':[ROOT/'dist/source-model-safety'],
        'geometry-sanitizer-build':[ROOT/'dist/surface-geometry'],
        'surface-snapshot-sanitizer-build':[ROOT/'dist/surface-snapshot-inactive'],
        'snapshot-layout-build':[ROOT/'dist/snapshot-layout'],
        'metadata-pages-sanitizer-build':[ROOT/'dist/metadata-pages-safety'],
        'c-example-build':[ROOT/'dist/c-smoke'],
        'browser':[evidence/'browser.json'],
        'accessibility-browser':[evidence/'browser-accessibility.json'],
        'selector-browser':[evidence/'selector-browser.json'],
        'task-graph-browser':[evidence/'task-graph.json'],
        'terminal':[evidence/'terminal.json',evidence/'terminal-state.json',evidence/'terminal-output.bin'],
        'selector-terminal':[evidence/'selector-terminal.json',evidence/'selector-terminal-state.json',evidence/'selector-terminal-output.bin'],
        'unicode-document-hosts':[evidence/'unicode-document-hosts'/'RESULTS.json']+[evidence/'unicode-document-hosts'/host/name for host in ['standalone','prompt-toolkit','bubbletea','ratatui'] for name in ['RESULTS.json','terminal.bin']]+[evidence/'unicode-document-hosts'/host/'scroll-terminal.bin' for host in ['standalone','prompt-toolkit']]+[evidence/'unicode-document-hosts'/host/name for host in ['bubbletea','ratatui'] for name in ['shift-navigation.bin','drag-selection.bin']]+[evidence/'unicode-document-hosts/ratatui/modal-roundtrip.bin'],
        'document-persistence':[evidence/'document-persistence'/name for name in ['RESULTS.json','roundtrip-pty.bin','rejected-pty.bin','saved-document.json','scene-switch-pty.bin','empty-scene-switch-pty.bin','scene-undo-pty.bin']] + [evidence/'document-persistence'/'standalone'/name for name in ['RESULTS.json','roundtrip-pty.bin','rejected-pty.bin','saved-document.json','scene-switch-pty.bin','empty-scene-switch-pty.bin','scene-undo-pty.bin']],
        'prompt-toolkit-host':[evidence/'framework.json',evidence/'framework-state.json',evidence/'framework-output.bin'],
        'benchmark':[evidence/'benchmark.json'],
        'capture':[evidence/'capture'],
    }
    if os.environ.get('NOCTURNE_COVERAGE')=='1':outputs['build'].append(ROOT/'dist/dependency-audit'/('libnocturne_native.dylib' if sys.platform=='darwin' else 'libnocturne_native.so'))
    for step in plan:
        if step[0].startswith('discovered-c-build-') and ('scripts/original_c_oracles.py' in step[1] or 'tests/observatory_overlay_safety.c' in step[1]):
            command=step[1]
            output=command[command.index('--output')+1] if '--output' in command else command[command.index('-o')+1]
            outputs[step[0]]=[ROOT/output]
    for step in plan:
        if step[0].startswith(('resource-ownership-wasm-','resource-ownership-browser-')) or step[0] in ('particle-choices-wasm','particle-choices-browser','text-curves-wasm','text-curves-browser','presentation-policies-wasm','presentation-policies-browser','end-policies-wasm','end-policies-browser','define-aliases-wasm','define-aliases-browser','boolean-truth-wasm','boolean-truth-browser','selector-policies-wasm','selector-policies-browser','geometry-policies-wasm','geometry-policies-browser','floor-colliders-wasm','floor-colliders-browser','field-policies-wasm','field-policies-browser','prompt-policies-wasm','prompt-policies-browser','lifecycle-policies-wasm','lifecycle-policies-browser','status-policies-wasm','status-policies-browser','window-policies-wasm','window-policies-browser','path-policies-wasm','path-policies-browser','pointer-cancel-wasm','pointer-cancel-browser','ink-policies-wasm','ink-policies-browser','draft-weather-wasm','draft-weather-browser','flight-policies-wasm','flight-policies-browser','surface-policies-wasm','surface-policies-browser','corona-wasm','corona-browser','observatory-wasm','observatory-browser','kinetic-wasm','kinetic-browser','atelier-wasm','atelier-browser','thermal-source-wasm','thermal-source-browser','world-source-wasm','world-source-browser','world-shell-source-wasm','world-shell-source-browser','studio-nova-wasm','studio-nova-browser','text-alphabet-wasm','text-alphabet-browser','text-seed-wasm','text-seed-browser','text-trails-wasm','text-trails-browser','text-controls-wasm','text-controls-browser','source-options-wasm','source-options-browser','widget-numeric-browser','event-example-guards-browser','window-source-wasm','window-source-browser'):
            outputs[step[0]]=[ROOT/step[1][-1]]
    cases=[{'id':step[0],'argv':step[1],'cwd':str(ROOT/(step[2] if len(step)>2 else '')),
             'timeoutSeconds':max(timeoutSeconds,STEP_TIMEOUT_FLOORS.get(step[0],0)),'logLimitBytes':64*1024*1024,
             'artifacts':[str(path) for path in outputs.get(step[0],[])]} for step in plan]
    # Every case executing an AddressSanitizer build output declares leak detection,
    # so neither a host default nor an inherited opt-out decides that gate.
    sanitized=addressSanitizedOutputs(plan);leakDetection=sanitizerRunEnvironment()
    for case in cases:
        if leakDetection and case['argv'] and os.path.normpath(Path(case['cwd'])/str(case['argv'][0])) in sanitized:
            case['environmentOverrides']=dict(leakDetection)
    for case in cases:
        if case['id'] in STEP_ENVIRONMENT_PINS:
            case['environmentOverrides']={**case.get('environmentOverrides',{}),**STEP_ENVIRONMENT_PINS[case['id']]}
    return cases


def publicTreeOmissions(root: Path = ROOT) -> set[str]:
    """Files, relative to native/, that the public tree left out with the fixture Gallery entries. The public tree
    records them in PUBLIC-TREE-REPORT.json beside native/ (tools/release/export_public_tree.py); a source tree has no
    such report and omits nothing, so a missing file there is still an error."""
    report=root.parent/'PUBLIC-TREE-REPORT.json'
    if not report.is_file():return set()
    return {entry['path'][len('native/'):] for entry in json.loads(report.read_text())['excluded'] if entry['path'].startswith('native/')}

def dropOmittedSteps(plan: list, omitted: set[str]) -> tuple[list, list[str]]:
    """The plan without the steps that name an omitted file (a path argument, or a unittest module of tests/), and the
    ids of the steps dropped, so the qualification scope declares them."""
    modules={Path(name).stem for name in omitted if name.startswith('tests/') and name.endswith('.py')}
    kept,dropped=[],[]
    for step in plan:
        named=any(str(argument) in omitted or str(argument).split('.')[0] in modules for argument in step[1])
        if named:dropped.append(step[0])
        else:kept.append(step)
    return kept,dropped

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=['exhaustive','rc2'],default='exhaustive',help='explicit release profile; exhaustive remains available')
    parser.add_argument('--strict',action='store_true',help='require four actual runtimes; hardware/art approval stays separate')
    parser.add_argument('--capture',action='store_true')
    parser.add_argument('--list',action='store_true')
    parser.add_argument('--rust-bin',type=Path,help='actual compiler bin directory; no shell startup edits')
    parser.add_argument('--evidence-dir',type=Path,help='fresh output directory; existing EXECUTION.json is refused')
    storage=parser.add_mutually_exclusive_group()
    storage.add_argument('--checkpoint-dir',type=Path,help='new external immutable per-case checkpoint store')
    storage.add_argument('--resume',type=Path,help='existing checkpoint store; use a new execution/evidence directory')
    parser.add_argument('--stop-after',help='pause after this case with a nonpassing partial receipt; requires checkpoint storage')
    parser.add_argument('--step-timeout',type=float,default=900,help='seconds allowed for each step; a case with a longer floor in STEP_TIMEOUT_FLOORS keeps that floor, which the flag can raise but not lower')
    parser.add_argument('--heartbeat',type=float,default=5)
    args=parser.parse_args()
    # Shadow-check builds are test-only (TDD-STATE-COPY-ELIMINATION section 5.7): refused before planning.
    if args.strict and 'NOCTURNE_SHADOW_CHECK' in os.environ:
        parser.error('NOCTURNE_SHADOW_CHECK is set: strict qualification refuses shadow-check builds; unset it')
    if not all(math.isfinite(value) and value>0 for value in [args.step_timeout,args.heartbeat]):
        parser.error('step timeout and heartbeat must be positive and finite')
    if args.stop_after and not (args.checkpoint_dir or args.resume):
        parser.error('--stop-after requires --checkpoint-dir or --resume')
    if args.rust_bin:
        directory=args.rust_bin.resolve()
        if not all((directory/name).is_file() for name in ['rustc','cargo']): parser.error('--rust-bin must contain rustc and cargo')
        os.environ['PATH']=str(directory)+os.pathsep+os.environ.get('PATH','')
    os.environ.setdefault('CARGO_NET_OFFLINE','true')
    os.environ.setdefault('CARGO_TERM_COLOR','never')
    # Explicit, not inherited by luck: before discovery, the step environment and the bound environment digest.
    os.environ['PYTHONPATH']=qualificationEnvironment(os.environ)['PYTHONPATH']
    from toolchain import discover
    tool=discover();cc=tool['cc'] or 'cc'
    sources=[str(p) for p in sorted((ROOT/'src').glob('*.c')) if p.name!='wasm_mem.c']
    typescript_module=os.environ.get('NOCTURNE_TYPESCRIPT_MODULE') or str(Path(shutil.which('tsc') or 'tsc').resolve().parent.parent/'lib/typescript.js')
    os.environ.setdefault('NOCTURNE_TYPESCRIPT_MODULE',typescript_module)
    from resource_ownership_plan import ownership_jobs,core_python_contracts
    omitted=publicTreeOmissions()
    ownership_count=1 if 'examples/resource-ownership-scenes.json' in omitted else max(1,(len(json.loads((ROOT/'examples/resource-ownership-scenes.json').read_text()))+63)//64)
    plan=[
        ('build',[sys.executable,'scripts/build.py']),
        ('gallery',[sys.executable,'scripts/build_gallery.py']),
        ('ci-policy',[sys.executable,'-m','unittest','discover','-s',str(ROOT.parent/'tools/ci'),'-p','test_*.py','-v']),
        ('gallery-option-inventory',['node','tests/gallery_option_coverage.test.mjs',typescript_module]),
        ('gallery-context-inventory',['node','tests/gallery_context_coverage.test.mjs',typescript_module]),
        ('gallery-worker-regressions',['node','--test','tests/gallery_parallel.test.mjs']),
        ('gallery-attract-policy',['node','--test','tests/gallery_attract.test.mjs']),
        ('gallery-attract-built',['node','--test','tests/gallery_attract_built.test.mjs']),
        ('gallery-studies',[sys.executable,'scripts/check_gallery_studies.py']),
        ('gallery-studies-wasm',['node','scripts/check_gallery_cases.mjs','evidence/gallery-study-cases.json','evidence/gallery-studies-wasm.json']),
        ('python-contracts',core_python_contracts(sys.executable,ownership_count)),
        # Named explicitly and not a test_*.py module, so the discovery in python-contracts never collects the replay (native/docs/BUILD-SCOPE.md).
        ('fingerprint-stability',[sys.executable,'-m','unittest','-v','qualification_fingerprint_stability_check'],'tests'),
        ('go-contracts',['go','test','-count=1','./...'],'bindings/go'),
        ('typescript-types',['tsc','--noEmit','--strict','--target','es2022','--module','nodenext','--moduleResolution','nodenext','examples/typed.ts','examples/selectors.ts','tests/types/selectors.ts','tests/types/surfaces.ts','tests/types/metadata.ts','tests/types/weather.ts','tests/types/transport.ts','tests/types/text.ts','tests/types/color_fields.ts','tests/types/source_optics.ts','tests/types/prompt_presentation.ts','tests/types/bidi_prompt.ts','tests/types/controller.ts','tests/types/graph_readback.ts','tests/types/electrical_graphs.ts','tests/types/firework_stages.ts','tests/types/world_shell_profiles.ts','tests/types/world_nova_optics.ts','tests/types/resource_animation_bindings.ts','tests/types/waterfall_composition.ts','tests/types/road_composition.ts','tests/types/garden_composition.ts','tests/types/retained_guard_gallery.ts','tests/types/appearance_gallery.ts','tests/types/condition_gallery.ts','tests/types/weather_gallery.ts','tests/types/presentation_gallery.ts','tests/types/material_gallery.ts','tests/types/interaction_gallery.ts','tests/types/scenic_appearance.ts','tests/types/scenic_public.ts','tests/types/floor_float.ts','tests/types/appearance_event_contract.ts','tests/types/typed_set_gallery.ts','tests/types/node_status_gallery.ts','tests/types/input_window_gallery.ts','tests/types/mesh_pointer.ts','tests/types/alpha_clock.ts','tests/types/curve_choices.ts','tests/types/unit_guards.ts','tests/types/binding_transitions.ts','tests/types/resource_ownership.ts','tests/types/particle_choices.ts','tests/types/text_curves.ts','tests/types/presentation_policies.ts','tests/types/end_policies.ts','tests/types/define_aliases.ts','tests/types/boolean_truth.ts','tests/types/selector_policies.ts','tests/types/geometry_policies.ts','tests/types/floor_colliders.ts','tests/types/field_policies.ts','tests/types/prompt_policies.ts','tests/types/lifecycle_policies.ts','tests/types/status_policies.ts','tests/types/window_policies.ts','tests/types/path_policies.ts','tests/types/pointer_cancel.ts','tests/types/ink_policies.ts','tests/types/draft_weather.ts','tests/types/flight_policies.ts','tests/types/surface_policies.ts','tests/types/corona.ts','tests/types/observatory.ts','tests/types/kinetic.ts','tests/types/atelier.ts','tests/types/thermal_profiles.ts','tests/types/world_profiles.ts','tests/types/world_shell_source.ts','tests/types/studio_nova.ts','tests/types/text_alphabet.ts','tests/types/text_seed.ts','tests/types/text_trails.ts','tests/types/text_controls.ts','tests/types/text_phase_model.ts','tests/types/material_patterns.ts','tests/types/source_options.ts','tests/types/widget_numeric_readback.ts','tests/types/event_example_guards.ts','tests/types/window_source_geometry.ts','tests/types/window_presentation.ts','tests/types/window_texture.ts','tests/types/window_content.ts','tests/types/source_stage_components.ts','tests/types/area_geometry.ts','tests/types/prompt_appearance.ts','tests/types/composition_project.mts']),
        ('generated-window-document-wasm',['node','bindings/typescript/generated-window-document.test.mjs']),
        ('source-text-phase-wasm',['node','bindings/typescript/text-phase-model.test.mjs']),
        ('area-geometry-wasm',['node','bindings/typescript/area-geometry.test.mjs']),
        ('prompt-presentation-wasm',['node','bindings/typescript/prompt-presentation.test.mjs']),
        ('bidi-prompt-wasm',['node','bindings/typescript/bidi-prompt.test.mjs']),
        ('source-optics-wasm',['node','bindings/typescript/source-optics.test.mjs']),
        ('soft-fronts-wasm',['node','bindings/typescript/soft-fronts.test.mjs']),
        ('color-fields-wasm',['node','bindings/typescript/color-fields.test.mjs']),
        ('wave-field-wasm',['node','bindings/typescript/wave.test.mjs']),
        ('ribbon-wasm',['node','bindings/typescript/ribbon.test.mjs']),
        ('flow-wasm',['node','bindings/typescript/flow.test.mjs']),
        ('waterfall-wasm',['node','bindings/typescript/waterfall.test.mjs']),
        ('surface-water-wasm',['node','bindings/typescript/surface_water.test.mjs']),
        ('thermal-wasm',['node','bindings/typescript/thermal.test.mjs']),
        ('cell-art-wasm',['node','bindings/typescript/cell_art.test.mjs']),
        ('trigger-expressions-wasm',['node','bindings/typescript/trigger-expressions.test.mjs']),
        ('large-geometry-wasm',['node','bindings/typescript/large-geometry.test.mjs']),
        ('panel-values-wasm',['node','bindings/typescript/panel-values.test.mjs']),
        ('value-lifetimes-wasm',['node','bindings/typescript/value-lifetimes.test.mjs']),
        ('numeric-expressions-wasm',['node','bindings/typescript/numeric-expressions.test.mjs']),
        ('expression-transforms-wasm',['node','bindings/typescript/expression-transforms.test.mjs']),
        ('resource-values-wasm',['node','bindings/typescript/resource-values.test.mjs']),
        ('panel-extensions-wasm',['node','bindings/typescript/panel-extensions.test.mjs']),
        ('value-rebinding-wasm',['node','bindings/typescript/value-rebinding.test.mjs']),
        ('value-descriptors-wasm',['node','bindings/typescript/value-descriptors.test.mjs']),
        ('flow-values-wasm',['node','bindings/typescript/flow-values.test.mjs']),
        ('surface-values-wasm',['node','bindings/typescript/surface-values.test.mjs']),
        ('wave-values-wasm',['node','bindings/typescript/wave-values.test.mjs']),
        ('float-values-wasm',['node','bindings/typescript/float-values.test.mjs']),
        ('shortcuts-wasm',['node','bindings/typescript/shortcuts.test.mjs']),
        ('text-run-identities-wasm',['node','bindings/typescript/text-run-identities.test.mjs']),
        ('scenic-output-ranges-wasm',['node','bindings/typescript/scenic-output-ranges.test.mjs']),
        ('flow-thickness-wasm',['node','bindings/typescript/flow-thickness.test.mjs']),
        ('foam-transport-wasm',['node','bindings/typescript/foam-transport.test.mjs']),
        ('foam-values-wasm',['node','bindings/typescript/foam-values.test.mjs']),
        ('mesh-appearance-wasm',['node','bindings/typescript/mesh-appearance.test.mjs']),
        ('character-rules-wasm',['node','bindings/typescript/character-rules.test.mjs']),
        ('composite-spaces-wasm',['node','bindings/typescript/composite-spaces.test.mjs']),
        ('character-snapshots-wasm',['node','bindings/typescript/character-snapshots.test.mjs']),
        ('character-timeline-wasm',['node','bindings/typescript/character-timeline.test.mjs']),
        ('json-object-keys-wasm',['node','bindings/typescript/json-object-keys.test.mjs']),
        ('cell-art-values-wasm',['node','bindings/typescript/cell-art-values.test.mjs']),
        ('indicator-string-wasm',['node','bindings/typescript/indicator-string.test.mjs']),
        ('bound-text-validation-wasm',['node','bindings/typescript/bound-text-validation.test.mjs']),
        ('queued-expression-ownership-wasm',['node','bindings/typescript/queued-expression-ownership.test.mjs']),
        ('scheduled-batches-wasm',['node','bindings/typescript/scheduled-batches.test.mjs']),
        ('value-registry-snapshots-wasm',['node','bindings/typescript/value-registry-snapshots.test.mjs']),
        ('resource-binding-snapshots-wasm',['node','bindings/typescript/resource-binding-snapshots.test.mjs']),
        ('widget-data-wasm',['node','bindings/typescript/widget-data.test.mjs']),
        ('widget-data-entries-wasm',['node','bindings/typescript/widget-data-entries.test.mjs']),
        ('data-ordering-wasm',['node','bindings/typescript/data-ordering.test.mjs']),
        ('material-tracks-wasm',['node','bindings/typescript/material-tracks.test.mjs']),
        ('host-events-wasm',['node','bindings/typescript/host-events.test.mjs']),
        ('payload-expressions-wasm',['node','bindings/typescript/payload-expressions.test.mjs']),
        ('typed-values-wasm',['node','bindings/typescript/typed-values.test.mjs']),
        ('data-expressions-wasm',['node','bindings/typescript/data-expressions.test.mjs']),
        ('structured-expressions-wasm',['node','bindings/typescript/structured-expressions.test.mjs']),
        ('json-number-codec-wasm',['node','bindings/typescript/json-number-codec.test.mjs']),
        ('value-subtrees-wasm',['node','bindings/typescript/value-subtrees.test.mjs']),
        ('material-bindings-wasm',['node','bindings/typescript/material-bindings.test.mjs']),
        ('value-addressing-wasm',['node','bindings/typescript/value-addressing.test.mjs']),
        ('vim-count-wasm',['node','bindings/typescript/vim_counts.test.mjs']),
        ('metadata-pages-typescript',['node','--test','bindings/typescript/metadata-pages.test.mjs']),
        ('sdk-contract',[sys.executable,'scripts/capture_sdk_contract.py','--output','evidence/SDK-CONTRACT.json']),
        ('rust-contracts',['cargo','test','--offline','--locked','--manifest-path','bindings/rust/Cargo.toml','--all-targets']),
        ('rust-doctests',['cargo','test','--offline','--locked','--manifest-path','bindings/rust/Cargo.toml','--doc']),
        ('rust-docs',['cargo','doc','--offline','--locked','--manifest-path','bindings/rust/Cargo.toml','--no-deps']),
        ('parity',[sys.executable,'scripts/parity.py']+(['--require-rust'] if args.strict else [])),
        ('unicode-conformance',[sys.executable,'scripts/check_unicode.py']),
        ('font-presentation',[sys.executable,'scripts/check_font_presentation.py']),
        ('graph-weather-browser',[sys.executable,'scripts/check_graph_weather_browser.py','--output','evidence/graph-weather-browser.json']),
        ('graph-readback-wasm',['node','bindings/typescript/graph-readback.test.mjs']),
        ('aggregate-fade-wasm',['node','bindings/typescript/aggregate-fade.test.mjs']),
        ('electrical-graphs-wasm',['node','bindings/typescript/electrical-graphs.test.mjs']),
        ('firework-stages-wasm',['node','bindings/typescript/firework-stages.test.mjs']),
        ('world-shell-profiles-wasm',['node','bindings/typescript/world-shell-profiles.test.mjs']),
        ('presentation-gallery-wasm',['node','bindings/typescript/presentation-gallery.test.mjs']),
        ('material-gallery-wasm',['node','bindings/typescript/material-gallery.test.mjs']),
        ('interaction-gallery-wasm',['node','bindings/typescript/interaction-gallery.test.mjs']),
        ('scenic-appearance-wasm',['node','bindings/typescript/scenic-appearance.test.mjs']),
        ('floor-float-wasm',['node','bindings/typescript/floor-float.test.mjs']),
        ('appearance-event-contract-wasm',['node','bindings/typescript/appearance-event-contract.test.mjs']),
        ('typed-set-gallery-wasm',['node','bindings/typescript/typed-set-gallery.test.mjs']),
        ('node-status-gallery-wasm',['node','bindings/typescript/node-status-gallery.test.mjs']),
        ('input-window-gallery-wasm',['node','bindings/typescript/input-window-gallery.test.mjs']),
        ('mesh-pointer-wasm',['node','bindings/typescript/mesh-pointer-contexts.test.mjs']),
        ('alpha-clock-wasm',['node','bindings/typescript/alpha-clock-contexts.test.mjs']),
        ('curve-choice-wasm',['node','bindings/typescript/curve-choice-gallery.test.mjs']),
        ('unit-guard-wasm',['node','bindings/typescript/unit-guard-gallery.test.mjs']),
        ('field-policies-wasm',['node','bindings/typescript/field-policy-gallery.test.mjs','evidence/field-policies-wasm.json']),
        ('field-policies-browser',[sys.executable,'scripts/check_field_policy_browser.py','--output','evidence/field-policies-browser.json']),
        ('prompt-policies-wasm',['node','bindings/typescript/prompt-policy-gallery.test.mjs','evidence/prompt-policies-wasm.json']),
        ('prompt-policies-browser',[sys.executable,'scripts/check_prompt_policy_browser.py','--output','evidence/prompt-policies-browser.json']),
        ('lifecycle-policies-wasm',['node','bindings/typescript/lifecycle-policy-gallery.test.mjs','evidence/lifecycle-policies-wasm.json']),
        ('lifecycle-policies-browser',[sys.executable,'scripts/check_lifecycle_policy_browser.py','--output','evidence/lifecycle-policies-browser.json']),
        ('status-policies-wasm',['node','bindings/typescript/status-policy-gallery.test.mjs','evidence/status-policies-wasm.json']),
        ('status-policies-browser',[sys.executable,'scripts/check_status_policy_browser.py','--output','evidence/status-policies-browser.json']),
        ('window-policies-wasm',['node','bindings/typescript/window-policy-gallery.test.mjs','evidence/window-policies-wasm.json']),
        ('window-policies-browser',[sys.executable,'scripts/check_window_policy_browser.py','--output','evidence/window-policies-browser.json']),
        ('path-policies-wasm',['node','bindings/typescript/path-policy-gallery.test.mjs','evidence/path-policies-wasm.json']),
        ('path-policies-browser',[sys.executable,'scripts/check_path_policy_browser.py','--output','evidence/path-policies-browser.json']),
        ('pointer-cancel-wasm',['node','bindings/typescript/pointer-cancel-gallery.test.mjs','evidence/pointer-cancel-wasm.json']),
        ('pointer-cancel-browser',[sys.executable,'scripts/check_pointer_cancel_browser.py','--output','evidence/pointer-cancel-browser.json']),
        ('ink-policies-wasm',['node','bindings/typescript/ink-policy-gallery.test.mjs','evidence/ink-policies-wasm.json']),
        ('ink-policies-browser',[sys.executable,'scripts/check_ink_policy_browser.py','--output','evidence/ink-policies-browser.json']),
        ('draft-weather-wasm',['node','bindings/typescript/draft-weather-gallery.test.mjs','evidence/draft-weather-wasm.json']),
        ('draft-weather-browser',[sys.executable,'scripts/check_draft_weather_browser.py','--output','evidence/draft-weather-browser.json']),
        ('flight-policies-wasm',['node','bindings/typescript/flight-policy-gallery.test.mjs','evidence/flight-policies-wasm.json']),
        ('flight-policies-browser',[sys.executable,'scripts/check_flight_policy_browser.py','--output','evidence/flight-policies-browser.json']),
        ('surface-policies-wasm',['node','bindings/typescript/surface-policy-gallery.test.mjs','evidence/surface-policies-wasm.json']),
        ('surface-policies-browser',[sys.executable,'scripts/check_surface_policy_browser.py','--output','evidence/surface-policies-browser.json']),
        ('corona-wasm',['node','bindings/typescript/corona-gallery.test.mjs','evidence/corona-wasm.json']),
        ('corona-browser',[sys.executable,'scripts/check_corona_browser.py','--output','evidence/corona-browser.json']),
        ('observatory-wasm',['node','bindings/typescript/observatory-gallery.test.mjs','evidence/observatory-wasm.json']),
        ('observatory-browser',[sys.executable,'scripts/check_observatory_browser.py','--output','evidence/observatory-browser.json']),
        ('window-source-wasm',['node','bindings/typescript/window-source-gallery.test.mjs','evidence/window-source-wasm.json']),
        ('window-source-browser',[sys.executable,'scripts/check_window_source_browser.py','--output','evidence/window-source-browser.json']),
        ('event-example-guards-browser',[sys.executable,'scripts/check_event_example_guards_browser.py','--output','evidence/event-example-guards-browser.json']),
        ('widget-numeric-browser',[sys.executable,'scripts/check_widget_numeric_browser.py','--output','evidence/widget-numeric-browser.json']),
        ('source-options-wasm',['node','bindings/typescript/source-options-gallery.test.mjs','evidence/source-options-wasm.json']),
        ('source-options-browser',[sys.executable,'scripts/check_source_options_browser.py','--output','evidence/source-options-browser.json']),
        ('text-controls-wasm',['node','bindings/typescript/text-controls-gallery.test.mjs','evidence/text-controls-wasm.json']),
        ('text-controls-browser',[sys.executable,'scripts/check_text_controls_browser.py','--output','evidence/text-controls-browser.json']),
        ('text-trails-wasm',['node','bindings/typescript/text-trails-gallery.test.mjs','evidence/text-trails-wasm.json']),
        ('text-trails-browser',[sys.executable,'scripts/check_text_trails_browser.py','--output','evidence/text-trails-browser.json']),
        ('text-seed-wasm',['node','bindings/typescript/text-seed-gallery.test.mjs','evidence/text-seed-wasm.json']),
        ('text-seed-browser',[sys.executable,'scripts/check_text_seed_browser.py','--output','evidence/text-seed-browser.json']),
        ('text-alphabet-wasm',['node','bindings/typescript/text-alphabet-gallery.test.mjs','evidence/text-alphabet-wasm.json']),
        ('text-alphabet-browser',[sys.executable,'scripts/check_text_alphabet_browser.py','--output','evidence/text-alphabet-browser.json']),
        ('studio-nova-wasm',['node','bindings/typescript/studio-nova-gallery.test.mjs','evidence/studio-nova-wasm.json']),
        ('studio-nova-browser',[sys.executable,'scripts/check_studio_nova_browser.py','--output','evidence/studio-nova-browser.json']),
        ('world-shell-source-wasm',['node','bindings/typescript/world-shell-source-gallery.test.mjs','evidence/world-shell-source-wasm.json']),
        ('world-shell-source-browser',[sys.executable,'scripts/check_world_shell_source_browser.py','--output','evidence/world-shell-source-browser.json']),
        ('world-source-wasm',['node','bindings/typescript/world-particle-gallery.test.mjs','evidence/world-source-wasm.json']),
        ('world-source-browser',[sys.executable,'scripts/check_world_particle_browser.py','--output','evidence/world-source-browser.json']),
        ('thermal-source-wasm',['node','bindings/typescript/thermal-gallery.test.mjs','evidence/thermal-source-wasm.json']),
        ('thermal-source-browser',[sys.executable,'scripts/check_thermal_browser.py','--output','evidence/thermal-source-browser.json']),
        ('atelier-wasm',['node','bindings/typescript/atelier-gallery.test.mjs','evidence/atelier-wasm.json']),
        ('atelier-browser',[sys.executable,'scripts/check_atelier_browser.py','--output','evidence/atelier-browser.json']),
        ('kinetic-wasm',['node','bindings/typescript/kinetic-gallery.test.mjs','evidence/kinetic-wasm.json']),
        ('kinetic-browser',[sys.executable,'scripts/check_kinetic_browser.py','--output','evidence/kinetic-browser.json']),
        ('floor-colliders-wasm',['node','bindings/typescript/floor-collider-gallery.test.mjs','evidence/floor-colliders-wasm.json']),
        ('floor-colliders-browser',[sys.executable,'scripts/check_floor_collider_browser.py','--output','evidence/floor-colliders-browser.json']),
        ('geometry-policies-wasm',['node','bindings/typescript/geometry-policy-gallery.test.mjs','evidence/geometry-policies-wasm.json']),
        ('geometry-policies-browser',[sys.executable,'scripts/check_geometry_policy_browser.py','--output','evidence/geometry-policies-browser.json']),
        ('selector-policies-wasm',['node','bindings/typescript/selector-policy-gallery.test.mjs','evidence/selector-policies-wasm.json']),
        ('selector-policies-browser',[sys.executable,'scripts/check_selector_policy_browser.py','--output','evidence/selector-policies-browser.json']),
        ('boolean-truth-wasm',['node','bindings/typescript/boolean-truth-gallery.test.mjs','evidence/boolean-truth-wasm.json']),
        ('boolean-truth-browser',[sys.executable,'scripts/check_boolean_truth_browser.py','--output','evidence/boolean-truth-browser.json']),
        ('define-aliases-wasm',['node','bindings/typescript/define-alias-gallery.test.mjs','evidence/define-aliases-wasm.json']),
        ('define-aliases-browser',[sys.executable,'scripts/check_define_alias_browser.py','--output','evidence/define-aliases-browser.json']),
        ('end-policies-wasm',['node','bindings/typescript/end-policy-gallery.test.mjs','evidence/end-policies-wasm.json']),
        ('end-policies-browser',[sys.executable,'scripts/check_end_policy_browser.py','--output','evidence/end-policies-browser.json']),
        ('lifecycle-end-matrix',[sys.executable,'-m','unittest','-v','test_lifecycle_end_matrix'],'tests'),
        ('presentation-policies-wasm',['node','bindings/typescript/presentation-policy-gallery.test.mjs','evidence/presentation-policies-wasm.json']),
        ('presentation-policies-browser',[sys.executable,'scripts/check_presentation_policy_browser.py','--output','evidence/presentation-policies-browser.json']),
        ('text-curves-wasm',['node','bindings/typescript/text-curve-gallery.test.mjs','evidence/text-curves-wasm.json']),
        ('text-curves-browser',[sys.executable,'scripts/check_text_curve_browser.py','--output','evidence/text-curves-browser.json']),
        ('particle-choices-wasm',['node','bindings/typescript/particle-choice-gallery.test.mjs','evidence/particle-choices-wasm.json']),
        ('particle-choices-browser',[sys.executable,'scripts/check_particle_choice_browser.py','--output','evidence/particle-choices-browser.json']),
        ('wide-unbound-values-wasm',['node','bindings/typescript/wide-unbound-values.test.mjs']),
        ('binding-transition-wasm',['node','bindings/typescript/binding-transition-gallery.test.mjs']),
        ('binding-transition-browser',[sys.executable,'scripts/check_binding_transition_browser.py','--output','evidence/binding-transition-browser.json']),
        ('unit-guard-browser',[sys.executable,'scripts/check_unit_guard_browser.py','--output','evidence/unit-guard-browser.json']),
        ('curve-choice-browser',[sys.executable,'scripts/check_curve_choice_browser.py','--output','evidence/curve-choice-browser.json']),
        ('alpha-clock-browser',[sys.executable,'scripts/check_alpha_clock_browser.py','--output','evidence/alpha-clock-browser.json']),
        ('default-clock-browser',[sys.executable,'scripts/check_default_clock_browser.py','--output','evidence/default-clock-browser.json']),
        ('mesh-pointer-browser',[sys.executable,'scripts/check_mesh_pointer_browser.py','--output','evidence/mesh-pointer-browser.json']),
        ('input-window-gallery-browser',[sys.executable,'scripts/check_input_window_browser.py','--output','evidence/input-window-gallery-browser.json']),
        ('node-status-gallery-browser',[sys.executable,'scripts/check_node_status_browser.py','--output','evidence/node-status-gallery-browser.json']),
        ('typed-set-gallery-browser',[sys.executable,'scripts/check_typed_set_browser.py','--output','evidence/typed-set-gallery-browser.json']),
        ('floor-float-browser',[sys.executable,'scripts/check_floor_float_browser.py','--output','evidence/floor-float-browser.json']),
        ('scenic-appearance-browser',[sys.executable,'scripts/check_scenic_appearance_browser.py','--output','evidence/scenic-appearance-browser.json']),
        ('selection-gallery-browser',[sys.executable,'scripts/check_selection_gallery_browser.py','--output','evidence/selection-gallery-browser.json']),
        ('ownership-gallery-browser',[sys.executable,'scripts/check_ownership_gallery_browser.py','--output','evidence/ownership-gallery-browser.json']),
        ('material-gallery-browser',[sys.executable,'scripts/check_material_gallery_browser.py','--output','evidence/material-gallery-browser.json']),
        ('presentation-gallery-browser',[sys.executable,'scripts/check_presentation_gallery_browser.py','--output','evidence/presentation-gallery-browser.json']),
        ('weather-gallery-wasm',['node','bindings/typescript/weather-gallery.test.mjs']),
        ('weather-gallery-browser',[sys.executable,'scripts/check_weather_gallery_browser.py','--output','evidence/weather-gallery-browser.json']),
        ('condition-gallery-wasm',['node','bindings/typescript/condition-gallery.test.mjs']),
        ('condition-gallery-browser',[sys.executable,'scripts/check_condition_gallery_browser.py','--output','evidence/condition-gallery-browser.json']),
        ('appearance-gallery-wasm',['node','bindings/typescript/appearance-gallery.test.mjs']),
        ('appearance-gallery-browser',[sys.executable,'scripts/check_appearance_gallery_browser.py','--output','evidence/appearance-gallery-browser.json']),
        ('retained-guard-wasm',['node','bindings/typescript/retained-guard-gallery.test.mjs']),
        ('retained-guard-browser',[sys.executable,'scripts/check_retained_guard_browser.py','--output','evidence/retained-guard-browser.json']),
        ('garden-composition-wasm',['node','bindings/typescript/garden-composition.test.mjs']),
        ('garden-composition-browser',[sys.executable,'scripts/check_garden_composition_browser.py','--output','evidence/garden-composition-browser.json']),
        ('road-composition-wasm',['node','bindings/typescript/road-composition.test.mjs']),
        ('road-composition-browser',[sys.executable,'scripts/check_road_composition_browser.py','--output','evidence/road-composition-browser.json']),
        ('waterfall-multiple-wasm',['node','bindings/typescript/waterfall-multiple.test.mjs']),
        ('waterfall-composition-wasm',['node','bindings/typescript/waterfall-composition.test.mjs']),
        ('waterfall-composition-browser',[sys.executable,'scripts/check_waterfall_composition_browser.py','--output','evidence/waterfall-composition-browser.json']),
        ('resource-animation-bindings-wasm',['node','bindings/typescript/resource-animation-bindings.test.mjs']),
        ('resource-animation-bindings-browser',[sys.executable,'scripts/check_resource_animation_browser.py','--output','evidence/resource-animation-bindings-browser.json']),
        ('world-nova-optics-wasm',['node','bindings/typescript/world-nova-optics.test.mjs']),
        ('world-nova-optics-browser',[sys.executable,'scripts/check_world_nova_optics_browser.py','--output','evidence/world-nova-optics-browser.json']),
        ('world-shell-browser',[sys.executable,'scripts/check_world_shell_browser.py','--output','evidence/world-shell-browser.json']),
        ('firework-birth-preservation',['node','bindings/typescript/firework-birth-preservation.test.mjs']),
        ('firework-stages-browser',[sys.executable,'scripts/check_firework_stage_browser.py','--output','evidence/firework-stages-browser.json']),
        ('electrical-graphs-browser',[sys.executable,'scripts/check_electrical_graph_browser.py','--output','evidence/electrical-graphs-browser.json']),
        ('retained-treatment-browser',[sys.executable,'scripts/check_retained_treatment_browser.py','--output','evidence/retained-treatment-browser.json']),
        ('controller-workflow-browser',[sys.executable,'scripts/check_controller_workflow_browser.py','--output','evidence/controller-workflow-browser.json']),
        ('emitter-control-browser',[sys.executable,'scripts/check_emitter_control_browser.py','--output','evidence/emitter-control-browser.json']),
        ('cleanup-workflow-browser',[sys.executable,'scripts/check_cleanup_workflow_browser.py','--output','evidence/cleanup-workflow-browser.json']),
        ('fluid-lifecycle-browser',[sys.executable,'scripts/check_fluid_lifecycle_browser.py','--output','evidence/fluid-lifecycle-browser.json']),
        ('state-workflow-browser',[sys.executable,'scripts/check_state_workflow_browser.py','--output','evidence/state-workflow-browser.json']),
        ('status-workflow-browser',[sys.executable,'scripts/check_status_workflow_browser.py','--output','evidence/status-workflow-browser.json']),
        ('input-workflow-browser',[sys.executable,'scripts/check_input_workflow_browser.py','--output','evidence/input-workflow-browser.json']),
        ('font-document-view',[sys.executable,'scripts/check_font_document_view.py','--output','evidence/font-document-view']),
        ('thermal-sample-wasm',['node','bindings/typescript/thermal-sample.test.mjs']),
        ('surface-water-add-wasm',['node','bindings/typescript/surface-water-add.test.mjs']),
        ('hull-immersion-wasm',['node','bindings/typescript/hull-immersion.test.mjs']),
        ('hull-plane-example',[sys.executable,'examples/hull_plane.py','--output','evidence/hull-plane-example.json','--frame','evidence/hull-plane-example.cells']),
        ('fluid-exchange-example',[sys.executable,'examples/fluid_exchange.py','--output','evidence/fluid-exchange-example.json','--frame','evidence/fluid-exchange-example.cells']),
        ('rotating-surface-example',[sys.executable,'examples/rotating_surface.py','--output','evidence/rotating-surface-example.json','--frames','evidence/rotating-surface-frames']),
        ('retained-float-hull-wasm',['node','bindings/typescript/retained-float-hull.test.mjs']),
        ('surface-fluid-wasm',['node','bindings/typescript/surface-fluid.test.mjs']),
        ('retained-angular-fluid-wasm',['node','bindings/typescript/retained-angular-fluid.test.mjs']),
        ('line-breaks-wasm',['node','bindings/typescript/linebreak.test.mjs']),
        ('script-runs-wasm',['node','bindings/typescript/script-runs.test.mjs']),
        ('reference-docs-coverage',[sys.executable,'-m','unittest','-v','test_reference_docs_coverage'],'tests'),
        ('source-examples',[sys.executable,'scripts/check_examples.py']),
        ('graph-consumers',[sys.executable,'scripts/check_graph_consumer.py']),
        ('field-equation-error',[sys.executable,'scripts/check_field_error.py']),
        ('native-dependencies',[sys.executable,'scripts/dependencies.py']),
        ('sanitizer-build',[cc,'-std=c11','-O1','-g','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-fno-strict-aliasing','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Iinclude','-Isrc',*sources,'tests/safety.c','-o','dist/native-safety']),
        ('sanitizer-run',[str(ROOT/'dist/native-safety')]),
        ('source-model-sanitizer-build',[cc,'-std=c11','-O1','-g','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-fno-strict-aliasing','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Iinclude','-Isrc',*sources,'tests/source_model_contract.c','-o','dist/source-model-safety']),
        ('source-model-sanitizer-run',[str(ROOT/'dist/source-model-safety')]),
        ('character-contracts-build',[cc,'-std=c11','-O1','-g','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-fno-strict-aliasing','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Iinclude','-Isrc',*sources,'tests/character_selector_contract.c','tests/character_owner_contract.c','tests/character_render_contract.c','tests/character_paint_contract.c','tests/character_effect_contract.c','tests/character_rule_contract.c','tests/character_registry_contract.c','tests/character_region_contract.c','tests/character_contracts.c','-o','dist/character-contracts']),
        ('character-contracts-run',[str(ROOT/'dist/character-contracts')]),
        ('geometry-sanitizer-build',[cc,'-std=c11','-O1','-g','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-fno-strict-aliasing','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Iinclude','-Isrc',*sources,'tests/surface_geometry.c','-o','dist/surface-geometry']),
        ('geometry-sanitizer-run',[str(ROOT/'dist/surface-geometry')]),
        ('surface-snapshot-sanitizer-build',[cc,'-std=c11','-O1','-g','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-fno-strict-aliasing','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Iinclude','-Isrc',*sources,'tests/surface_snapshot_inactive.c','-o','dist/surface-snapshot-inactive']),
        ('surface-snapshot-sanitizer-run',[str(ROOT/'dist/surface-snapshot-inactive')]),
        ('metadata-pages-sanitizer-build',[cc,'-std=c11','-O1','-g','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-fno-strict-aliasing','-fsanitize=address,undefined','-fno-omit-frame-pointer','-Iinclude','-Isrc',*sources,'tests/metadata_pages.c','-o','dist/metadata-pages-safety']),
        ('metadata-pages-sanitizer-run',[str(ROOT/'dist/metadata-pages-safety')]),
        ('snapshot-layout-build',[cc,'-std=c11','-O2','-ffp-contract=off','-fno-fast-math','-fno-math-errno','-fno-strict-aliasing','-Iinclude','-Isrc',*sources,'tests/snapshot_layout.c','-o','dist/snapshot-layout']),
        ('snapshot-layout-run',[str(ROOT/'dist/snapshot-layout')]),
        ('c-example-build',[cc,'-std=c11','-Iinclude','examples/native_smoke.c','-Ldist','-lnocturne_native','-Wl,-rpath,'+str(ROOT/'dist'),'-o','dist/c-smoke']),
        ('c-example-run',[str(ROOT/'dist/c-smoke')]),
        ('workshop-browser',[sys.executable,'scripts/check_workshop_browser.py','--gallery',str(ROOT/'Nocturne-RC4-Source-Build.html'),'--output',str(ROOT/'evidence/workshop-browser')]),
        ('area-geometry-browser',[sys.executable,'scripts/check_area_geometry_browser.py','--output','evidence/area-geometry-browser.json']),
        ('prompt-presentation-browser',[sys.executable,'scripts/check_prompt_presentation_browser.py','--output','evidence/prompt-presentation-browser.json']),
        ('bidi-prompt-browser',[sys.executable,'scripts/check_bidi_prompt_browser.py','--output','evidence/bidi-prompt-browser.json']),
        ('source-optics-browser',[sys.executable,'scripts/check_source_optics_browser.py','--output','evidence/source-optics-browser.json']),
        ('soft-fronts-browser',[sys.executable,'scripts/check_soft_fronts_browser.py','--output','evidence/soft-fronts-browser.json']),
        ('color-fields-browser',[sys.executable,'scripts/check_color_fields_browser.py','--output','evidence/color-fields-browser.json']),
        ('browser',[sys.executable,'scripts/check_browser.py']),
        ('accessibility-browser',[sys.executable,'scripts/check_browser_accessibility.py']),
        ('selector-browser',[sys.executable,'scripts/check_selectors_browser.py']),
        ('task-graph-browser',[sys.executable,'scripts/check_task_graph.py']),
        ('terminal',[sys.executable,'scripts/check_terminal.py']),
        ('selector-terminal',[sys.executable,'scripts/check_selectors_terminal.py']),
        ('prompt-toolkit-host',[sys.executable,'scripts/check_framework.py']),
        ('unicode-document-hosts',[sys.executable,'scripts/check_unicode_document_hosts.py']),
        ('document-persistence',[sys.executable,'scripts/check_document_persistence.py']),
        ('benchmark',[sys.executable,'scripts/benchmark.py'])]
    # Include every authored type contract in the existing strict compiler pass.
    for step in plan:
        name, command = step[:2]
        if name == 'typescript-types':
            present = set(command)
            fixtures = sorted(p for p in (ROOT/'tests/types').glob('*.ts')
                              if p.is_file() and not p.name.endswith('.d.ts'))
            additional = [p for p in (ROOT/'tests/types').iterdir()
                          if p.is_file() and p.suffix in {'.mts', '.cts'}
                          and not p.name.endswith(('.d.mts', '.d.cts'))]
            additional.extend(p for p in (ROOT/'bindings/typescript').iterdir()
                              if p.is_file() and p.name.endswith(('-types.ts', '-types.mts', '-types.cts')))
            fixtures.extend(sorted(additional))
            for fixture in fixtures:
                relative = fixture.relative_to(ROOT).as_posix()
                if relative not in present:
                    command.append(relative)
                    present.add(relative)
    # Discover standalone WASM suites so newly authored tests cannot be omitted.
    ownershipPlan=ownership_jobs(sys.executable,ownership_count)
    scheduled={str(arg) for step in [*plan,*ownershipPlan] for arg in step[1]}
    for suite in sorted((ROOT/'bindings/typescript').glob('*test.mjs')):
        relative=suite.relative_to(ROOT).as_posix()
        if relative not in scheduled:plan.append((discoveredCaseId('wasm',relative),['node',relative]))
    # Retain standalone C entry points, including historical schema contracts.
    for suite in sorted((ROOT/'tests').glob('*.c')):
        relative=suite.relative_to(ROOT).as_posix()
        if relative in scheduled or not re.search(r'\bint\s+main\s*\(',suite.read_text()):continue
        executable='dist/discovered-'+suite.stem
        jobs=originalOracleJobs(ROOT,cc,sys.executable,relative,executable,sources)
        build,run=jobs if jobs is not None else ([cc,'-std=c11','-O1','-fno-math-errno','-Iinclude','-Isrc',*sources,relative,'-o',executable],[str(ROOT/executable)])
        plan.extend([(discoveredCaseId('c-build',relative),build),(discoveredCaseId('c-run',relative),run)])
    if args.capture: plan.append(('capture',[sys.executable,'scripts/capture.py']))
    plan.extend(ownershipPlan)
    plan,publicTreeOmitted=dropOmittedSteps(plan,omitted)
    qualificationScope={'profile':'exhaustive','exhaustive':not publicTreeOmitted,'omittedCaseIds':publicTreeOmitted}
    if args.profile=='rc2':
        from rc2_release_plan import select_rc2_plan,rc2_scope
        fullPlan=plan;plan=select_rc2_plan(fullPlan,python=sys.executable,native_root=ROOT,omitted_files=omitted,omitted_cases=publicTreeOmitted)
        qualificationScope=rc2_scope(fullPlan,plan)
        qualificationScope['omittedCaseIds']=[*publicTreeOmitted,*qualificationScope['omittedCaseIds']]
    cases=checkpointPlan(plan,args.step_timeout)
    if args.stop_after and args.stop_after not in {case['id'] for case in cases}:
        parser.error('--stop-after must name a declared case; use --list')
    if args.list:
        print(json.dumps(cases,indent=2));return 0
    evidence=ROOT/'evidence';evidence.mkdir(exist_ok=True)
    out=(args.evidence_dir or evidence/('run-'+time.strftime('%Y%m%dT%H%M%S')+'-'+str(os.getpid()))).resolve()
    checkpointDirectory=(args.checkpoint_dir or args.resume)
    if checkpointDirectory:
        checkpointDirectory=checkpointDirectory.absolute()
        if checkpointDirectory.resolve().is_relative_to(ROOT.parent):
            parser.error('checkpoint storage must be outside the source repository')
        if (checkpointDirectory==out or checkpointDirectory.is_relative_to(out) or out.is_relative_to(checkpointDirectory)):
            parser.error('checkpoint storage and execution/evidence directories must be disjoint')
    before=fingerprint();versions={}
    from cargo_example import cargoEnvironment
    environment=cargoEnvironment(ROOT.parent,os.environ)
    for name,argv in [('python',[sys.executable,'--version']),('cc',[cc,'--version']),('clang',[tool['wasmCC'] or 'clang','--version']),('wasm-ld',[tool['wasmLD'] or 'wasm-ld','--version']),('node',['node','--version']),('go',['go','version']),('rust',['rustc','-vV']),('cargo',['cargo','--version']),('typescript',['tsc','--version'])]:
        try:
            r=subprocess.run(argv,capture_output=True,text=True,timeout=15,env=environment)
            versions[name]={'argv':argv,'exitCode':r.returncode,'output':r.stdout.splitlines()[:10],'stderr':r.stderr.splitlines()[:10]}
        except (OSError,subprocess.TimeoutExpired) as error: versions[name]={'status':'BLOCKED','reason':str(error)}
    def currentBinding():
        actualEnvironment=dict(os.environ)
        return {'schema':'nocturne.native.qualification-binding.v1','source':fingerprint(),
                'plan':cases,'qualificationScope':qualificationScope,'toolchains':versions,'toolExecutables':toolExecutables(tool,actualEnvironment),
                'environmentSha256':bindingDigest(actualEnvironment),'platform':platform.platform(),
                'architecture':platform.machine(),'host':socket.gethostname(),
                'policy':{'strict':args.strict,'capture':args.capture,'fullRC4Qualified':False}}
    binding=currentBinding()
    def interrupted(signum,frame): raise KeyboardInterrupt(f'received signal {signum}')
    old=signal.signal(signal.SIGTERM,interrupted)
    result={};run=None
    try:
        with ExitStack() as stack:
            run=stack.enter_context(RunJournal(out,args.heartbeat))
            run.record.update(sourceBefore=before['sha256'],toolchains=versions,
                              toolExecutables=binding['toolExecutables'],environmentSha256=binding['environmentSha256'],
                              platform=platform.platform(),expectedSteps=len(plan),expectedCaseIds=[case['id'] for case in cases])
            run.write()
            checkpoints=stack.enter_context(CheckpointStore(checkpointDirectory,binding,resume=bool(args.resume))) if checkpointDirectory else None
            if checkpoints: checkpoints.bindRun(run)
            run.write()
            atomicJson(evidence/'BUILD-VERIFICATION.json',{'schema':'nocturne.native.verification.v2','status':'RUNNING','complete':False,'runDirectory':str(out),'sourceBefore':before['sha256'],'localBuildVerified':False,'fourRuntimeVerified':False,'fullRC4Qualified':False})
            for case in cases:
                if checkpoints: checkpoints.runCase(run,case['id'],currentBinding,env=environment)
                else: run.runStep(case['id'],case['argv'],Path(case['cwd']),timeoutSeconds=case['timeoutSeconds'],env=environment,environmentOverrides=case.get('environmentOverrides'))
                if case['id']=='build' and run.record['commands'][-1]['status']!='PASS':break
                if args.stop_after==case['id']: break
            after=fingerprint();same=before['sha256']==after['sha256'];commands=run.record['commands']
            complete=[row['id'] for row in commands]==[case['id'] for case in cases]
            local=complete and all(r['status']=='PASS' for r in commands if not r['id'].startswith('rust-'))
            allPassed=complete and all(r['status']=='PASS' for r in commands)
            parityFile=ROOT/'evidence/parity.json'
            parityCase=next((row for row in commands if row['id']=='parity' and row['status']=='PASS'),None)
            if parityCase and checkpoints: parityFile=checkpoints.artifact('parity',parityFile)
            parity=json.loads(parityFile.read_text()) if parityCase and parityFile.exists() else {}
            # The applied build switches, as the build step retained them (build_switches.py).
            switchFile=ROOT/'dist/build-switches.json'
            buildCase=next((row for row in commands if row['id']=='build' and row['status']=='PASS'),None)
            if buildCase and checkpoints: switchFile=checkpoints.artifact('build',switchFile)
            buildSwitches=json.loads(switchFile.read_text()) if buildCase and switchFile.exists() else None
            switchProblem=buildSwitchesProblem(buildSwitches,args.strict)
            if switchProblem: allPassed=False;local=False
            allFour=allPassed and bool(parity.get('fourRuntimePassed'))
            from runtime_qualification import runtimePlanQualified
            runtimeQualified=runtimePlanQualified(complete=complete,sourceUnchanged=same,
                strict=args.strict,capture=args.capture,expectedCaseIds=[case['id'] for case in cases],
                commands=commands,fourRuntimePassed=parity.get('fourRuntimePassed'))
            result={'schema':'nocturne.native.verification.v2','status':'FAIL' if any(row['status']!='PASS' for row in commands) else 'PAUSED' if not complete else 'PASS' if same and allPassed else 'FAIL','complete':complete,'sourceBefore':before['sha256'],'sourceAfter':after['sha256'],'sourceUnchanged':same,'sourceChanges':sorted(p for p in set(before['files'])|set(after['files']) if before['files'].get(p)!=after['files'].get(p)),'platform':platform.platform(),'toolchains':versions,'toolExecutables':binding['toolExecutables'],'environmentSha256':binding['environmentSha256'],'commands':commands,'localBuildVerified':same and local,'fourRuntimeVerified':same and allFour,'fullRC4Qualified':False,'seconds':round(time.monotonic()-run.started,3),'runDirectory':str(out),'expectedCaseIds':[case['id'] for case in cases],'checkpointDirectory':str(checkpointDirectory) if checkpointDirectory else None,'checkpointBindingSha256':bindingDigest(binding) if checkpoints else None,'remainingReleaseGates':[]}
            result['buildSwitches']=buildSwitches
            if switchProblem: result.update(status='FAIL',buildSwitchesProblem=switchProblem)
            galleryPath=ROOT/'Nocturne-RC4-Source-Build.html'
            if allPassed and galleryPath.is_file():result['gallery']={'path':'native/Nocturne-RC4-Source-Build.html','bytes':galleryPath.stat().st_size,'sha256':fileDigest(galleryPath)}
            # The journal is strict: any blocked group prevents PASS. The outer
            result.update(qualificationProfile=args.profile,qualificationScope=qualificationScope,runtimePlanQualified=runtimeQualified,
                runtimePolicy={'strict':args.strict,'capture':args.capture},
                remainingReleaseGates=['Source-matching final production coverage and ratchet',
                    'Required available host and historical software checks',
                    'Remaining mandatory implementation and independent distribution integrity'],
                nonblockingPendingRecords=['Hardware tests, human decisions and operator-dependent remote checks under RELEASE-POLICY-2026-10-06.md'])
            # CLI can explicitly return the narrower local-build outcome.
            metadata={'sourceAfter':after['sha256'],'sourceUnchanged':same,'fourRuntimeVerified':result['fourRuntimeVerified'],'fullRC4Qualified':False}
            metadata['runtimePlanQualified']=runtimeQualified
            if checkpoints: checkpoints.finish(run,same and allPassed,currentBinding,**metadata)
            else: run.finish(same and allPassed,completePlan=complete,**metadata)
            if checkpoints: result['checkpointSummary']=run.record['checkpointSummary']
            atomicJson(evidence/'BUILD-VERIFICATION.json',result)
            atomicJson(out/'BUILD-VERIFICATION.json',result)
    except BaseException as error:
        failure={'schema':'nocturne.native.verification.v2','status':'INTERRUPTED' if isinstance(error,KeyboardInterrupt) else 'FAIL','complete':False,'runDirectory':str(out),'sourceBefore':before['sha256'],'reason':str(error),'localBuildVerified':False,'fourRuntimeVerified':False,'fullRC4Qualified':False}
        atomicJson(evidence/'BUILD-VERIFICATION.json',failure)
        if run is not None: atomicJson(out/'BUILD-VERIFICATION.json',failure)
        raise
    finally: signal.signal(signal.SIGTERM,old)
    print(json.dumps({k:result[k] for k in ['complete','sourceUnchanged','localBuildVerified','fourRuntimeVerified','fullRC4Qualified','seconds']},indent=2))
    return 0 if result['localBuildVerified'] and (not args.strict or result['fourRuntimeVerified']) else 2
if __name__=='__main__':raise SystemExit(main())
