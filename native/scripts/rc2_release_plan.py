"""Explicit RC2 qualification selection; no execution or coverage claims."""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import sys

REQUIRED_CASE_IDS=(
 'build','gallery','fingerprint-stability','go-contracts','typescript-types','rust-contracts','rust-doctests','rust-docs',
 'parity','native-dependencies','sanitizer-build','sanitizer-run',
 'source-model-sanitizer-build','source-model-sanitizer-run',
 'geometry-sanitizer-build','geometry-sanitizer-run',
 'snapshot-layout-build','snapshot-layout-run','c-example-build','c-example-run','sdk-contract',
 # Readiness re-audit 2026-11-01: acceptance checks that justify repairs execute in the release receipt.
 'gallery-attract-policy','gallery-attract-built','lifecycle-end-matrix','reference-docs-coverage',
)
# The native Python modules run as three steps, so that each finishes well inside the 900 s step timeout: one
# 900 s step timed out on the Linux qualification host (receipt linux-deviant-20261115/qualify-rc2-01) with about
# 520 tests done. Measured serially on the macOS workstation the modules take about 94 s in the core step,
# about 113 s in the acceptance step and about 102 s in the runtimes step; the Linux host did the first ~516 tests, which
# take about 260 s here, in 900 s, so it runs roughly 3.5 times slower and each step should need about 350 s there. Every module is in exactly one step (test_rc2_release_plan); add a new module to the lightest.
NATIVE_CORE_MODULES=(
 'test_prompt_appearance','test_rc2_camera_braille','test_camera_controls',
 'test_camera_controls_migration','test_scene_art_clock','test_camera_anchor_default','test_braille_floor_regressions',
 'test_braille_fidelity','test_braille_capture_ticks','test_source_model','test_model_gallery_resources','test_source_modal',
 'test_rc2_native_display_copy','test_product_copy','test_rc2_parity_plan','test_rc2_package','test_rc2_shipping','test_workshop_metadata','test_rc2_sdk_check','test_sdk_shipping_core','test_readme','test_github_site',
 # Fresh-host guards (receipt native/evidence/linux-host-20261031/qualify-rc2-02): no workstation
 # paths, uniform repository-root bootstrap, qualifier-supplied PYTHONPATH.
 'test_host_portability','test_repository_root_bootstrap','test_qualification_python_path',
 # Receipt native/evidence/macos-host-20261110/qualify-rc2-01: every third-party import the plan
 # executes is pinned in tools/requirements-qualification.txt.
 'test_qualification_requirements',
 # The replay is its own plan step (REQUIRED_CASE_IDS); this guards that step's command, deadline,
 # exclusion from discovery and refusal to pass when it did not run.
 'test_fingerprint_stability_plan',
 # Release identity guard (re-audit 2026-11-01).
 'test_release_identity',
 # Operator directive 2026-11-01: hybrid dictates one class per object and never replaces U+28FF.
 'test_hybrid_sampling_invariant',
 # Thresholds and registration of the live gallery pacing check (rc2-gallery-pacing).
 'test_gallery_pacing_check',
 # Bulk-memory lowering and byte-loop results of the WASM memory routines (per-command State copies).
 'test_wasm_memory_routines',
)
NATIVE_ACCEPTANCE_MODULES=(
 # Session acceptance matrices (re-audit 2026-11-01).
 'test_first_prompt_source','test_v01_prompt_surfaces','test_language_contracts_acceptance','test_status_notifications_acceptance',
 # Readiness row SDK-8: the enabled source-stage scene follows the viewport past 512x256.
 'test_source_stage_extent',
)
NATIVE_RUNTIME_MODULES=(
 # Public 1.0.0: provenance-gated Gallery admission, and a Workshop export that draws the same frame in WASM,
 # Python, Go and Rust (TypeScript type-checked).
 'test_gallery_admission','test_project_export_languages',
 # Environment occlusionTint and occludedDots: base and prototype frame oracles, snapshots, bindings, four runtimes.
 'test_occlusion_tint',
 # Bounded prompt source layer: base frame oracles, archived kernel inside the layer, growth, snapshots, four runtimes.
 'test_bounded_prompt_source',
)
NATIVE_STEPS=(('rc2-native',NATIVE_CORE_MODULES),('rc2-native-acceptance',NATIVE_ACCEPTANCE_MODULES),('rc2-native-runtimes',NATIVE_RUNTIME_MODULES))
NATIVE_MODULES=tuple(name for _,group in NATIVE_STEPS for name in group)
BROWSER_MODULES=('test_composition_gallery','test_camera_controls_gallery','test_rc2_generated_window_adapter','test_gallery_product','test_occlusion_gallery','test_gallery_weather_controls')
# Its own step: the camera acceptance sweep is too long to share a native step's timeout.
CAMERA_SPACE_MODULE='test_camera_coordinate_space_acceptance'
# Live pacing of the built gallery in Chromium (catch-up, frame rate, hidden-tab resume); a browser step beside rc2-browser.
PACING_CHECK='scripts/check_gallery_pacing.py'
NODE_SOURCES=('bindings/typescript/composition-project.test.mjs','bindings/typescript/composition-codegen.test.mjs','bindings/typescript/composition-presets.test.mjs','bindings/typescript/source-model.test.mjs')
OMITTED_SCOPES=(
 'Full Python discovery and every historical migration/oracle suite',
 'Exhaustive native/WASM gallery option combinations and recipe-wide browser sweep',
 'Unselected standalone WASM and C discovery cases',
 'Movie capture, benchmark, framework PTY matrix and exhaustive Unicode conformance',
 'Hosted CI, virtual machines and hardware presentation',
)

def select_rc2_plan(full_plan, *, python=sys.executable, native_root=None, omitted_files=frozenset(), omitted_cases=()):
 """Retain exact existing commands and add named current regressions.

 ``full_plan`` is qualify.py's complete tuple declaration after discovery.
 The caller still uses the normal journal, fingerprint and checkpoint logic.
 Missing sources/cases are errors, not skipped checks. The one exception is a public tree, which leaves out the fixture
 Gallery entries and the checks that need them: qualify.py passes what the tree's PUBLIC-TREE-REPORT.json lists
 (``omitted_files`` relative to native/, ``omitted_cases`` as step ids), and only those are tolerated.
 """
 native_root=Path(native_root or Path(__file__).resolve().parents[1])
 rows=list(full_plan);names=[row[0] for row in rows]
 if len(names)!=len(set(names)):raise ValueError('Duplicate full-plan case identity')
 missing=set(REQUIRED_CASE_IDS)-set(names)-set(omitted_cases)
 native_steps=[(step,tuple(name for name in group if 'tests/'+name+'.py' not in omitted_files)) for step,group in NATIVE_STEPS]
 browser_modules=tuple(name for name in BROWSER_MODULES if 'tests/'+name+'.py' not in omitted_files)
 camera_space=(CAMERA_SPACE_MODULE,) if 'tests/'+CAMERA_SPACE_MODULE+'.py' not in omitted_files else ()
 if missing:raise ValueError('Missing required RC2 cases: '+', '.join(sorted(missing)))
 required_sources=[*NODE_SOURCES,'scripts/build_reference_docs.py','tests/test_reference_docs.py','tests/test_reference_docs_coverage.py','tests/test_rc2_release_plan.py','tests/qualification_fingerprint_stability_check.py',PACING_CHECK]
 required_sources.extend('tests/'+name+'.py' for name in (*(name for _,group in native_steps for name in group),*browser_modules,*camera_space))
 for name in required_sources:
  if name not in omitted_files and not (native_root/name).is_file():raise FileNotFoundError(native_root/name)
 selected=[]
 for row in rows:
  if row[0] not in REQUIRED_CASE_IDS:continue
  item=deepcopy(row)
  if item[0]=='parity':
   if '--profile' in item[1]:raise ValueError('Full parity command already selects a profile')
   item=(item[0],[*item[1],'--profile','rc2'],*item[2:])
  selected.append(item)
 if [row[0] for row in selected[:2]]!=['build','gallery']:
  raise ValueError('RC2 build and gallery must be first in the full plan')
 selected.extend([
  *[(step,[python,'-m','unittest','-v',*group],'tests') for step,group in native_steps if group],
  *([('rc2-camera-space',[python,'-m','unittest','-v',CAMERA_SPACE_MODULE],'tests')] if camera_space else []),
  ('rc2-project-codegen',['node','--test',*NODE_SOURCES]),
  *([('rc2-browser',[python,'-m','unittest','-v',*browser_modules],'tests')] if browser_modules else []),
  ('rc2-gallery-pacing',[python,PACING_CHECK]),
  ('rc2-reference-docs',[python,'-m','unittest','-v','test_reference_docs','test_reference_docs_coverage'],'tests'),
  ('rc2-reference-validate',[python,'scripts/build_reference_docs.py','--check']),
  ('rc2-plan-regressions',[python,'-m','unittest','-v','test_rc2_release_plan'],'tests'),
 ])
 if len({row[0] for row in selected})!=len(selected):raise ValueError('RC2 case identity collides with full plan')
 return selected

def rc2_scope(full_plan, selected):
 """A scope declaration, deliberately without execution status or PASS flags."""
 included=[row[0] for row in selected];ids=set(included)
 return {
  'schema':'nocturne.qualification-scope.v1','profile':'rc2','exhaustive':False,
  'includedCaseIds':included,
  'omittedCaseIds':[row[0] for row in full_plan if row[0] not in ids],
  'omittedScopes':list(OMITTED_SCOPES),
  'coverageSeparate':True,
  'coveragePolicy':'Run the unchanged coverage gate with the actual measured profiles; the 70 percent minimum and any higher tracked/protected ratchet remain required.',
  'deliveryChecksSeparate':['Canonical package membership/hash verification','Extracted SDK build and runtime verification'],
 }
