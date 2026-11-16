"""The PTY broker must forward bytes, resize, and reap its child, not interpret."""
import base64,json,os,pathlib,selectors,subprocess,sys,time,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
class PtyBrokerTest(unittest.TestCase):
 def runChild(self,script,commands=()):
  p=subprocess.Popen([sys.executable,str(ROOT/'integrations/pty/pty_broker.py'),'--columns','73','--rows','21','--',sys.executable,'-c',script],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  self.addCleanup(lambda:p.poll() is None and p.kill());out=b'';records=[];sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ);deadline=time.monotonic()+5;sent=False;buffer=b''
  while time.monotonic()<deadline:
   for key,_ in sel.select(.1):
    chunk=os.read(key.fileobj.fileno(),65536)
    if not chunk:break
    buffer+=chunk
    while b'\n' in buffer:
     line,buffer=buffer.split(b'\n',1);row=json.loads(line);records.append(row)
     if row['type']=='output':out+=base64.b64decode(row['data'])
   if b'READY' in out and not sent:
    for command in commands:p.stdin.write((json.dumps(command)+'\n').encode())
    p.stdin.flush();sent=True
   if any(r['type']=='exit' for r in records):break
  if not any(r['type']=='exit' for r in records):p.kill();self.fail('child did not terminate: '+repr(out)+p.stderr.read().decode())
  p.wait(timeout=2);p.stdin.close();p.stdout.close();p.stderr.close();sel.close();return out,records
 def testControllingTty(self):
  out,rows=self.runChild("import os; print(os.isatty(0)); print(os.get_terminal_size()); print('READY');")
  self.assertIn(b'True',out);self.assertIn(b'columns=73',out);self.assertEqual(rows[-1]['code'],0)
 def testByteInputAndResize(self):
  cmd=[{'type':'resize','columns':99,'rows':33},{'type':'input','data':base64.b64encode('héllo\n'.encode()).decode()}]
  out,_=self.runChild("import os; print('READY',flush=True); s=input(); print(repr(s)); print(os.get_terminal_size());",cmd)
  self.assertIn('héllo'.encode(),out);self.assertIn(b'columns=99',out)
 def testNonzeroExit(self):
  _,rows=self.runChild("raise SystemExit(7)");self.assertEqual(rows[-1]['code'],7)
 def testEchoOffNotOptimisticallyEchoed(self):
  script="import termios; t=termios.tcgetattr(0); t[3]&=~termios.ECHO;termios.tcsetattr(0,termios.TCSANOW,t);print('READY',flush=True);s=input();print('length',len(s));"
  out,_=self.runChild(script,[{'type':'input','data':base64.b64encode(b'secret123\n').decode()}]);self.assertNotIn(b'secret123',out);self.assertIn(b'length 9',out)
 def testInterrupt(self):
  out,rows=self.runChild("import time; print('READY',flush=True);time.sleep(30)",[{'type':'input','data':'Aw=='}]);self.assertNotEqual(rows[-1]['code'],0)
if __name__=='__main__':unittest.main()
