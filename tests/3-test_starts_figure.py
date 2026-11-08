import base64
from fractions import Fraction as F
import importlib.util
import json
import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zlib
from betlab import starts_demo
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render_starts',ROOT/'examples/render_starts.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class StartFigureTests(unittest.TestCase):
    def setUp(self):
        self.r=starts_demo();self.s=(ROOT/'assets/start-allocation.svg').read_text();self.root=ET.fromstring(self.s)
        self.ids={e.attrib['id']:e for e in self.root.iter() if 'id'in e.attrib}
    def test_exact_bytes_metadata_and_tamper(self):
        self.assertEqual(m.render(self.r),self.s)
        self.assertEqual(json.loads(zlib.decompress(base64.b64decode(self.ids['report-zlib-base64'].text))),self.r)
        self.r['fair_null']['root_witness']['slack']='99/7'
        self.assertNotEqual(m.render(self.r),self.s)
    def test_all_fifty_coordinates(self):
        for k,values in (('scheduled',['1']+[a['wealth'] for a in self.r['delayed_signal']['trace']]),
                         ('from_start',['1']+[a['mixture'] for a in self.r['from_start_control']['trace']])):
            e=self.ids['curve-'+k];points=e.attrib['points'].split();self.assertEqual(len(points),25)
            self.assertEqual(json.loads(e.attrib['data-values']),values)
            for t,(p,v) in enumerate(zip(points,values)):
                x,y=map(float,p.split(','));self.assertAlmostEqual(x,95+38*t,places=3)
                self.assertAlmostEqual(y,425-31*math.log2(1+float(F(v))),places=3)
    def test_nine_cells_and_positions(self):
        vals={'delayed-cross':self.r['delayed_signal']['decision']['first_crossing'],
              'delayed-final':self.r['delayed_signal']['decision']['final_wealth'],
              'delayed-reserve':self.r['delayed_signal']['trace'][15]['unstarted_budget']}
        for k in ('fair_null','negative_drift_null'):
            for field in ('crossing_probability','expected_final_wealth','expected_stopped_wealth'):
                vals[k+'-'+field]=self.r[k]['summary'][field]
        self.assertEqual(len(vals),9)
        for k,v in vals.items():
            e=self.ids['cell-'+k];self.assertEqual(e.text,str(v));self.assertEqual(e.attrib['data-value'],str(v))
        for k,x in [('delayed-cross','52'),('delayed-final','385'),('delayed-reserve','710')]:
            self.assertEqual(self.ids['cell-'+k].attrib['x'],x)
            self.assertEqual(self.ids['cell-'+k].attrib['y'],'580')
