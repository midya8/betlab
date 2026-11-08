import base64
from fractions import Fraction as F
import importlib.util
import json
import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zlib
from betlab import demo
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render_demo',ROOT/'examples/render_demo.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class FigureTests(unittest.TestCase):
    def setUp(self):
        self.report=demo();self.text=(ROOT/'assets/evidence-audit.svg').read_text();self.root=ET.fromstring(self.text)
        self.byid={e.attrib['id']:e for e in self.root.iter() if 'id'in e.attrib}
    def test_byte_exact_and_complete_metadata(self):
        self.assertEqual(m.render(self.report),self.text)
        s=self.byid['report-zlib-base64'].text
        self.assertEqual(json.loads(zlib.decompress(base64.b64decode(s))),self.report)
    def test_every_curve_coordinate(self):
        for key in ('mixture','predictable','invalid_restart'):
            curve=self.byid['curve-'+key];points=curve.attrib['points'].split()
            values=['1']+[r[key] for r in self.report['cross_then_reverse']['trace']]
            self.assertEqual(json.loads(curve.attrib['data-values']),values)
            self.assertEqual(len(points),21)
            for t,(p,v) in enumerate(zip(points,values)):
                x,y=map(float,p.split(','));self.assertAlmostEqual(x,95+46*t,places=3)
                self.assertAlmostEqual(y,430-30*math.log2(1+float(F(v))),places=3)
    def test_all_nine_cells_and_hidden_tamper(self):
        for k,s in self.report['fair_coin_audit']['summary'].items():
            for field in ('crossing_probability','expected_final_wealth','expected_stopped_wealth'):
                el=self.byid[f'cell-{k}-{field}'];self.assertEqual(el.text,s[field]);self.assertEqual(el.attrib['data-value'],s[field])
        self.report['fair_coin_audit']['root_witness']['slack']['mixture']='99'
        self.assertNotEqual(m.render(self.report),self.text)
