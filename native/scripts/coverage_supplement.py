#!/usr/bin/env python3
"""Run the ten retained material/Kinetic/Atelier/Thermal tests as one journaled coverage step.

The runtime plan omits these equation/control/replay paths; their instrumented
profiles are written into the same fresh profile directory the plan used so the
unchanged coverage gate measures one combined set. No threshold is changed here.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1]
TESTS=('test_source_material_integration.RetainedMaterialPatterns.test_all_twelve_kinds_match_actual_original_wasm_at_absolute_2d_cells',
 'test_source_material_integration.RetainedMaterialPatterns.test_custom_focus_rotation_palette_controls_match_source_samples',
 'test_material_pattern_retention.MaterialPatternRetention.test_original_defaults_partial_edits_owned_metadata_and_clear',
 'test_material_pattern_retention.MaterialPatternRetention.test_complete_controls_and_scheduled_snapshot_replay',
 'test_kinetic_profiles.KineticProfiles.test_all_source_primitive_tables_and_exact_replay',
 'test_kinetic_profiles.KineticProfiles.test_negative_source_control_domains_are_atomic',
 'test_atelier_profiles.AtelierProfiles.test_all_five_source_equations_phase_boundaries_and_replay',
 'test_atelier_profiles.AtelierProfiles.test_negative_original_controls_are_atomic',
 'test_thermal_profiles.ThermalProfiles.test_original_geometry_burnout_delays_and_replay',
 'test_thermal_profiles.ThermalProfiles.test_negative_controls_are_atomic')
SCOPE='Ten existing material, Kinetic, Atelier and Thermal equation/control/replay tests; separate measured coverage phase'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def plan_argv(python):return [str(python),'-B','-m','unittest','-v',*TESTS]
def check_directories(output,profiles):
 output=Path(output);profiles=Path(profiles)
 if (output/'EXECUTION.json').exists():raise FileExistsError(str(output/'EXECUTION.json'))
 if not profiles.is_dir():raise ValueError('Profile directory from the completed runtime plan is required: '+str(profiles))
 if list(profiles.glob('*.profraw')) and os.environ.get('NOCTURNE_SUPPLEMENT_APPEND')!='1':raise FileExistsError('Profiles already present; set NOCTURNE_SUPPLEMENT_APPEND=1 to add the supplement to a completed plan directory')
def main():
 from delivery_runner import RunJournal
 from qualify import fingerprint
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--profiles',type=Path,required=True);a=p.parse_args()
 out=a.output.resolve();profiles=a.profiles.resolve();check_directories(out,profiles)
 if os.environ.get('NOCTURNE_COVERAGE')!='1':raise SystemExit('NOCTURNE_COVERAGE=1 instrumented environment required')
 env=dict(os.environ);env['LLVM_PROFILE_FILE']=str(profiles/'supplement-%m-%p.profraw');env['NOCTURNE_FRESH_PROFILE_DIR']=str(profiles)
 artifacts={name:sha(ROOT/'dist'/name)for name in('libnocturne_native.dylib'if sys.platform=='darwin'else'libnocturne_native.so','nocturne_native.wasm')}
 before=fingerprint()['sha256'];existing={p.name for p in profiles.glob('*.profraw')}
 with RunJournal(out,5)as run:
  run.record.update(sourceBefore=before,sourceCommit=subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],text=True).strip(),measuredArtifacts=artifacts,expectedSteps=1,scope=SCOPE,profileDirectory=str(profiles));run.write()
  run.runStep('source-equations-controls-replay',plan_argv(sys.executable),ROOT/'tests',timeoutSeconds=180,env=env)
  after=fingerprint()['sha256'];same=after==before and artifacts=={name:sha(ROOT/'dist'/name)for name in artifacts}
  new=sorted(p.name for p in profiles.glob('*.profraw')if p.name not in existing)
  passed=same and bool(new) and run.record['commands'][0]['status']=='PASS'
  run.finish(passed,sourceAfter=after,sourceUnchanged=after==before,artifactsUnchanged=same,measuredProfiles=new)
 print(json.dumps({'passed':passed,'newProfiles':len(new),'seconds':run.record['commands'][0]['seconds']}))
 return 0 if passed else 2
if __name__=='__main__':raise SystemExit(main())
