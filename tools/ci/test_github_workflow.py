import json,os,re,subprocess,sys,tempfile,unittest
from pathlib import Path
BASE=Path(__file__).resolve().parents[2]
import yaml
class WorkflowTests(unittest.TestCase):
 def setUp(self):
  self.raw=(BASE/'.github/workflows/nocturne.yml').read_text();self.w=yaml.load(self.raw,Loader=yaml.BaseLoader)
 def test_events_permissions_and_actual_commit(self):
  self.assertEqual(set(self.w['on']),{'push','pull_request','workflow_dispatch'})
  self.assertEqual(self.w['permissions'],{'contents':'read'})
  for name in ('native','supplemental','ratchet'):
   j=self.w['jobs'][name];self.assertLessEqual(int(j['timeout-minutes']),360)
   c=j['steps'][0];self.assertEqual(c['with']['ref'],'${{ github.sha }}');self.assertEqual(c['with']['persist-credentials'],'false')
 def test_verified_pins(self):
  pins={r['repository']:r['commit'] for r in json.loads((BASE/'tools/ci/action-pins.json').read_text())}
  for j in self.w['jobs'].values():
   for s in j['steps']:
    if 'uses' in s:
     name,sha=s['uses'].split('@');self.assertRegex(sha,r'^[0-9a-f]{40}$');self.assertEqual(pins[name],sha)
 def test_original_gates_preserved(self):
  n='\n'.join(s.get('run','') for s in self.w['jobs']['native']['steps']);q='\n'.join(s.get('run','') for s in self.w['jobs']['supplemental']['steps'])
  self.assertIn('sh qualify-native.sh --strict --capture',n);self.assertIn('coverage_gate.py',n)
  for v in ('sh build-native.sh','check_tdfiglet.py','qualify_dependency_hosts.py','native/hosts/ratatui/qualify.py','run_historical_tests.py','cargo_artifact.py'):self.assertIn(v,q)
  for v in ('prompt-toolkit','terminal-kit','bubbletea','ratatui'):self.assertIn('--host '+v,q)
  self.assertNotIn('package_contracts.py',self.raw);self.assertNotIn('continue-on-error',self.raw)
 def test_final_requires_both(self):
  j=self.w['jobs']['qualification'];self.assertEqual(j['needs'],['native','supplemental']);self.assertEqual(j['if'],'always()')
  body=j['steps'][0]['run']
  for v in ('native','supplemental'):self.assertIn('needs.'+v+'.result',body)
  self.assertEqual(body.count('= success'),2)
 def test_protected_ratchet_only(self):
  j=self.w['jobs']['ratchet'];self.assertEqual(j['needs'],['native','supplemental']);self.assertEqual(j['permissions'],{'contents':'write'})
  for v in ("github.event_name == 'push'",'refs/heads/main','refs/heads/integration'):self.assertIn(v,j['if'])
  self.assertEqual(self.raw.count('NOCTURNE_CI_TOKEN:'),1)
  d=next(s for s in j['steps'] if s.get('uses','').startswith('actions/download-artifact@'))
  for v in ('github.run_id','github.run_attempt','github.sha'):self.assertIn(v,d['with']['name'])
 def test_isolation_retention(self):
  for name in ('native','supplemental'):
   j=self.w['jobs'][name];self.assertEqual(j['env']['CARGO_BUILD_JOBS'],'2');self.assertEqual(j['env']['NOCTURNE_GALLERY_WORKERS'],'4')
   setup=next(s['run'] for s in j['steps'] if s.get('name')=='Task-scoped hosted-runner paths')
   for v in ('GITHUB_REPOSITORY','GITHUB_SHA','RUNNER_ARCH'):self.assertIn(v,setup)
   self.assertNotIn('runner.',json.dumps(j['env']))
   a=next(s for s in j['steps'] if s.get('uses','').startswith('actions/upload-artifact@'))
   self.assertEqual(a['if'],'always()');self.assertEqual(a['with']['if-no-files-found'],'error');self.assertIn('go work init',json.dumps(j))
   if name=='supplemental':self.assertNotIn('NOCTURNE_COVERAGE',j['env'])
   else:self.assertEqual(j['env']['NOCTURNE_COVERAGE'],'1')
 def test_all_github_job_envs_use_available_contexts(self):
  for path in sorted((BASE/'.github/workflows').glob('*.yml')):
   workflow=yaml.load(path.read_text(),Loader=yaml.BaseLoader)
   for name,job in workflow['jobs'].items():
    for value in job.get('env',{}).values():
     for expression in re.findall(r'\$\{\{(.*?)\}\}',str(value)):
      with self.subTest(workflow=path.name,job=name,expression=expression):
       self.assertNotRegex(expression,r'\brunner\s*\.','runner context is unavailable in jobs.<job_id>.env')
 def test_manual_paths_execute_with_actual_runner_temp(self):
  workflow=yaml.load((BASE/'.github/workflows/rc4-native.yml').read_text(),Loader=yaml.BaseLoader)
  step=next((s for s in workflow['jobs']['native']['steps'] if s.get('name')=='Task-scoped manual-runner paths'),None)
  self.assertIsNotNone(step)
  self.assertEqual(step['shell'],'bash')
  self.assertEqual(workflow['jobs']['native']['steps'][0],step)
  with tempfile.TemporaryDirectory(prefix='nocturne runner ') as directory:
   target=Path(directory)/'actual.env';env=os.environ.copy();env.update(RUNNER_TEMP=directory,GITHUB_ENV=str(target))
   result=subprocess.run(['/bin/bash','-eu','-o','pipefail','-c',step['run']],env=env,text=True,capture_output=True)
   self.assertEqual(result.returncode,0,result.stderr)
   actual=dict(line.split('=',1) for line in target.read_text().splitlines())
   self.assertEqual(actual,{'CARGO_HOME':directory+'/nocturne-cargo','CARGO_TARGET_DIR':directory+'/nocturne-targets/native','GOMODCACHE':directory+'/nocturne-go-modules','GOCACHE':directory+'/nocturne-go-build'})
 def test_tdf_source_is_a_repository_variable_with_no_default(self):
  for path in ('.github/workflows/nocturne.yml','.forgejo/workflows/nocturne.yml'):
   workflow=yaml.load((BASE/path).read_text(),Loader=yaml.BaseLoader)
   steps=[s for j in workflow['jobs'].values() for s in j['steps'] if s.get('name')=='Actual TDF isolated and application scenes']
   with self.subTest(path=path):
    self.assertEqual(len(steps),1)
    step=steps[0]
    self.assertEqual(step['if'],"${{ vars.NOCTURNE_TDFIGLET_REPOSITORY != '' }}",'the step runs only where the repository is configured')
    self.assertEqual(step['env'],{'NOCTURNE_TDFIGLET_REPOSITORY':'${{ vars.NOCTURNE_TDFIGLET_REPOSITORY }}'})
    self.assertIn('https://github.com/$NOCTURNE_TDFIGLET_REPOSITORY.git',step['run'])
    self.assertEqual(re.findall(r'github\.com/[\w.-]+/[\w.-]+',step['run']),[],'no repository is named in the step')
 def test_actual_shell_syntax(self):
  for path in sorted((BASE/'.github/workflows').glob('*.yml')):
   workflow=yaml.load(path.read_text(),Loader=yaml.BaseLoader)
   for j in workflow['jobs'].values():
    for s in j['steps']:
     if 'run' in s:
      shell=re.sub(r'\$\{\{.*?\}\}','CI_EXPRESSION',s['run']);r=subprocess.run(['/bin/bash','-n'],input=shell,text=True,capture_output=True)
      self.assertEqual(r.returncode,0,path.name+': '+s.get('name','')+r.stderr)
if __name__=='__main__':unittest.main()
