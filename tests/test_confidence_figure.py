import base64
import copy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zlib
from betlab import confidence_demo
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render_confidence',ROOT/'examples/render_confidence.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
NS={'s':'http://www.w3.org/2000/svg'}
class ConfidenceFigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=confidence_demo();cls.text=module.render(cls.r);cls.root=ET.fromstring(cls.text)
    def test_all_92_coordinates_and_exact_values(self):
        count=0
        for key,y0 in (('constant_positive',132),('reversal',488)):
            rows=self.r[key]['trace'];n=len(rows)
            for suffix in ('current','running'):
                p=self.root.find(f"s:polyline[@id='curve-{key}-{suffix}']",NS)
                vals=['-1']+[r['certificate']['lower'] if suffix=='current' else r['running_lower'] for r in rows]
                self.assertEqual(json.loads(p.attrib['data-values']),vals)
                pts=p.attrib['points'].split();self.assertEqual(len(pts),n+1)
                for t,(pair,v) in enumerate(zip(pts,vals)):
                    x,y=map(float,pair.split(','));self.assertAlmostEqual(x,94+930*t/n,delta=.00051);self.assertAlmostEqual(y,y0+235-80*(1+float(F(v))),delta=.00051);count+=1
        self.assertEqual(count,92)
    def test_seven_cells_and_readable_positions(self):
        expected={}
        for key in ('constant_positive','reversal'):
            for side,value in zip(('lower','upper'),self.r[key]['final_boundary_bracket']):expected[key+'-'+side]=value
        a=self.r['finite_coverage_audit'];expected.update(leaves=a['leaf_count'],exclusion=a['exclusion_probability'],crossing=a['crossing_probability'])
        for k,v in expected.items():
            e=self.root.find(f"s:text[@id='cell-{k}']",NS);self.assertEqual(e.text,str(v));self.assertEqual(e.attrib['data-value'],str(v));self.assertTrue(20<float(e.attrib['x'])<1050);self.assertTrue(20<float(e.attrib['y'])<1180)
    def test_full_metadata_hidden_tamper_and_exact_regeneration(self):
        blob=self.root.find("s:metadata[@id='report-zlib-base64']",NS).text
        self.assertEqual(json.loads(zlib.decompress(base64.b64decode(blob))),self.r)
        changed=copy.deepcopy(self.r);changed['finite_coverage_audit']['leaves'][0]['mass']='99/7'
        self.assertNotEqual(module.render(changed),self.text);self.assertEqual((ROOT/'assets/confidence-inversion.svg').read_text(),self.text)
