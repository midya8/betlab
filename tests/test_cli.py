import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from betlab import demo, replay, paired, audit_tree

ROOT=Path(__file__).resolve().parents[1]


class CLITests(unittest.TestCase):
    def run_cli(self,*args):
        return subprocess.run([sys.executable,'-m','betlab',*args],capture_output=True,cwd=ROOT)
    def test_demo_artifact(self):
        p=self.run_cli('demo');self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout),demo())
        self.assertEqual(p.stdout,(ROOT/'examples/demo.json').read_bytes())
    def test_three_inputs(self):
        for mode,fn in (('replay',replay),('paired',paired),('tree',audit_tree)):
            path=ROOT/'examples'/f'{mode}-input.json';x=json.loads(path.read_text());x.pop('schema_version')
            if mode=='replay':expected=fn(x.pop('differences'),**x)
            elif mode=='paired':expected=fn(x.pop('baseline'),x.pop('candidate'),**x)
            else:expected=fn(x.pop('tree'),**x)
            p=self.run_cli(mode,str(path));self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(json.loads(p.stdout),expected)
    def test_bad_input_empty_stdout(self):
        for raw in (b'{}',b'{"schema_version":true,"differences":[]}',
                    b'{"schema_version":1,"differences":[NaN]}',
                    b'{"schema_version":1,"differences":[0.1]}',
                    b'{"schema_version":1,"differences":[],"extra":0}',
                    b'{"schema_version":1,"differences":[],"differences":[]}',
                    b'\xff',b' '*200001):
            with tempfile.NamedTemporaryFile() as f:
                f.write(raw);f.flush();p=self.run_cli('replay',f.name)
            self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'');self.assertTrue(p.stderr.startswith(b'error:'))
    def test_bad_arguments(self):
        for args in ((),('bad',),('replay','/missing-betlab-input'),('demo','x')):
            p=self.run_cli(*args);self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'')
