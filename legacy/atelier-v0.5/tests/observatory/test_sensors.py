"""Test-first fixtures: sensors must label real readings and omit missing data."""
import importlib.util, pathlib, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('system_sensors',ROOT/'sensors/system_sensors.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class SensorsTest(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=pathlib.Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def write(self,path,text):p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(str(text))
 def testMissingIsAbsent(self):self.assertEqual(module.SystemSampler(self.root).poll(0),[])
 def testUnitsAndUnavailable(self):
  self.write('sys/class/hwmon/hwmon0/temp1_input','42000');self.write('sys/class/hwmon/hwmon0/power1_input','65000000');self.write('sys/class/hwmon/hwmon0/temp2_input','not available')
  rows=module.SystemSampler(self.root).poll(1000);self.assertEqual(sorted(r['value'] for r in rows),[42.0,65.0]);self.assertTrue(all(r['quality']=='measured' for r in rows))
 def testNetworkNeedsTwoSamples(self):
  self.write('proc/net/dev','eth0: 1000 0 0 0 0 0 0 0 2000 0 0 0 0 0 0 0\n');s=module.SystemSampler(self.root);self.assertEqual(s.poll(0),[])
  self.write('proc/net/dev','eth0: 2001000 0 0 0 0 0 0 0 1002000 0 0 0 0 0 0 0\n');rows=s.poll(1000);self.assertEqual(sorted(r['value'] for r in rows),[8.0,16.0])
 def testPowerWrapAndSequence(self):
  self.write('sys/class/powercap/intel-rapl:0/energy_uj',990000);self.write('sys/class/powercap/intel-rapl:0/max_energy_range_uj',1000000);s=module.SystemSampler(self.root);s.poll(0)
  self.write('sys/class/powercap/intel-rapl:0/energy_uj',10000);rows=s.poll(1000);self.assertEqual(rows[0]['value'],.02);self.assertEqual(rows[0]['unit'],'W')
 def testAccelScale(self):
  self.write('sys/bus/iio/devices/iio:device0/in_accel_scale','.1');self.write('sys/bus/iio/devices/iio:device0/in_accel_x_raw','20');rows=module.SystemSampler(self.root).poll(0);self.assertEqual(rows[0]['value'],2)
if __name__=='__main__':unittest.main()
