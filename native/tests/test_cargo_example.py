"""Cargo's emitted executable, not a guessed target path, identifies the built example."""
from pathlib import Path
import json, os, subprocess, sys, tempfile, unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
try:
    from cargo_example import buildExample, executableFromMessages
except ImportError:
    buildExample = executableFromMessages = None

def observedAlive(pid):
    """Observe a real child; never use a canned compiler or process response."""
    import select
    try:os.kill(pid,0)
    except ProcessLookupError:return False
    except PermissionError:return True
    if hasattr(os,'pidfd_open'):
        try:
            descriptor=os.pidfd_open(pid)
            try:return not bool(select.select([descriptor],[],[],0)[0])
            finally:os.close(descriptor)
        except ProcessLookupError:return False
        except OSError:pass
    # Only a /proc view of this PID namespace can describe these captured child
    # IDs. If no stronger observation exists, a live kernel PID stays nonpassing.
    try:
        if int(Path('/proc/self/stat').read_text().split(' ',1)[0])==os.getpid():
            return Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1][0] not in ('Z','X')
    except FileNotFoundError:return False
    return True

class CargoExampleTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform.startswith('linux'), 'actual Linux process liveness')
    def testProcessObservationDistinguishesLiveAndExitedChild(self):
        child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)'])
        try:
            self.assertTrue(observedAlive(child.pid),'new sleeping child must be observed alive')
            child.kill();child.wait(timeout=5)
            self.assertFalse(observedAlive(child.pid),'reaped child must be observed exited in its actual PID namespace')
        finally:
            if child.poll() is None:child.kill();child.wait(timeout=5)
    def testRealCargoExternalTargetAndUnchangedLock(self):
        self.assertIsNotNone(buildExample)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve(); project = root / 'project'; project.mkdir()
            (project/'examples').mkdir()
            (project/'Cargo.toml').write_text('[package]\nname="nocturne-execution-probe"\nversion="0.0.0"\nedition="2021"\n')
            (project/'Cargo.lock').write_text('version = 4\n\n[[package]]\nname = "nocturne-execution-probe"\nversion = "0.0.0"\n')
            lock = (project/'Cargo.lock').read_bytes()
            (project/'examples/probe.rs').write_text('fn main() { println!("COMPILED_CURRENT_EXAMPLE"); }\n')
            stale = project/'target/debug/examples/probe'; stale.parent.mkdir(parents=True)
            stale.write_text('STALE_DO_NOT_USE')
            env = {**os.environ, 'CARGO_TARGET_DIR':str(root/'external-target'), 'CARGO_NET_OFFLINE':'true'}
            exe = buildExample(project/'Cargo.toml', 'probe', root/'build.log', env=env)
            self.assertTrue(exe.is_relative_to(root/'external-target'))
            self.assertEqual(subprocess.check_output([str(exe)], env=env, text=True).strip(), 'COMPILED_CURRENT_EXAMPLE')
            self.assertEqual((project/'Cargo.lock').read_bytes(),lock)
            self.assertEqual(stale.read_text(),'STALE_DO_NOT_USE')
    def testFailedRealCompileNeverReturnsPriorExecutable(self):
        self.assertIsNotNone(buildExample)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d).resolve(); (root/'examples').mkdir()
            (root/'Cargo.toml').write_text('[package]\nname="broken-probe"\nversion="0.0.0"\nedition="2021"\n')
            (root/'Cargo.lock').write_text('version = 4\n\n[[package]]\nname = "broken-probe"\nversion = "0.0.0"\n')
            (root/'examples/probe.rs').write_text('compile_error!("intentional-negative-build"); fn main() {}\n')
            env = {**os.environ, 'CARGO_TARGET_DIR':str(root/'external-target')}
            with self.assertRaises(subprocess.CalledProcessError):
                buildExample(root/'Cargo.toml','probe',root/'build.log',env=env)
            record=json.loads((root/'build.json').read_text())
            self.assertEqual(record['status'],'FAIL');self.assertNotEqual(record['exitCode'],0)
            self.assertNotIn('executable',record)

    @unittest.skipUnless(sys.platform.startswith('linux'), 'Linux process-group observation')
    def testTimedOutCargoBuildScriptDescendantsAreStopped(self):
        # A real Cargo build script creates a child. It is not a mock compiler.
        import signal, time, select
        self.assertIsNotNone(buildExample)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d).resolve();(root/'examples').mkdir()
            (root/'Cargo.toml').write_text('[package]\nname="timeout-probe"\nversion="0.0.0"\nedition="2021"\n')
            (root/'Cargo.lock').write_text('version = 4\n\n[[package]]\nname = "timeout-probe"\nversion = "0.0.0"\n')
            (root/'examples/probe.rs').write_text('fn main() {}\n')
            pidPath=root/'build-child-pids.txt'
            (root/'build.rs').write_text('fn main(){let mut child=std::process::Command::new("sleep").arg("60").spawn().unwrap();'
                'std::fs::write(std::env::var("PROBE_PID_PATH").unwrap(),format!("{} {}",std::process::id(),child.id())).unwrap();'
                'child.wait().unwrap();}\n')
            env={**os.environ,'CARGO_TARGET_DIR':str(root/'external-target'),'PROBE_PID_PATH':str(pidPath)}
            pids=[]
            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    buildExample(root/'Cargo.toml','probe',root/'build.log',env=env,timeout=4)
                self.assertTrue(pidPath.exists(),'build script must have executed before timeout')
                pids=[int(x) for x in pidPath.read_text().split()]
                deadline=time.monotonic()+1
                while any(observedAlive(pid) for pid in pids) and time.monotonic()<deadline:
                    select.select([],[],[],.02)
                self.assertFalse(any(observedAlive(pid) for pid in pids),'Cargo build-script descendants survived timeout')
                record=json.loads((root/'build.json').read_text())
                self.assertEqual(record['status'],'TIMEOUT');self.assertIsInstance(record['exitCode'],int)
                self.assertNotIn('executable',record)
            finally:
                # Reap the deliberately exposed OLD-helper failure, never count this as helper cleanup.
                for pid in pids:
                    try:os.kill(pid,signal.SIGKILL)
                    except ProcessLookupError:pass

    def testMissingOrAmbiguousArtifactRejects(self):
        self.assertIsNotNone(executableFromMessages)
        row = lambda path: json.dumps({'reason':'compiler-artifact','target':{'name':'probe','kind':['example']},'executable':path})
        for text in ['', row('/one')+'\n'+row('/two')]:
            with self.assertRaises(ValueError): executableFromMessages(text,'probe')
    def testNonExampleCannotBeSelected(self):
        self.assertIsNotNone(executableFromMessages)
        text = json.dumps({'reason':'compiler-artifact','target':{'name':'probe','kind':['bin']},'executable':'/wrong'})
        with self.assertRaises(ValueError):executableFromMessages(text,'probe')
    def testDuplicateCargoMessageForSamePathIsNotAmbiguous(self):
        self.assertIsNotNone(executableFromMessages)
        with tempfile.TemporaryDirectory() as d:
            path=Path(d).resolve()/'probe';path.write_text('test')
            text=json.dumps({'reason':'compiler-artifact','target':{'name':'probe','kind':['example']},'executable':str(path)})
            self.assertEqual(executableFromMessages(text+'\n'+text,'probe'),path)

if __name__=='__main__':unittest.main()
