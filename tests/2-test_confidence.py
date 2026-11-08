import copy
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from betlab import confidence_sequence, mean_evidence, confidence_demo, replay
ROOT=Path(__file__).resolve().parents[1]


def direct(ds,m,bets,weights):
    vals=[]
    for b in bets:
        v=F(1)
        for d in ds:v*=1+b*(d-m)/2
        vals.append(v)
    return vals,sum(w*v for w,v in zip(weights,vals))


class ConfidenceTests(unittest.TestCase):
    def check_certificate(self,ds,cert,bets,weights,threshold,iterations):
        lo,hi=F(cert['lower']),F(cert['upper'])
        self.assertLessEqual(lo,hi);self.assertLessEqual(hi-lo,F(2,2**iterations))
        for key in ('left_witness','right_witness'):
            w=cert[key]
            if w is None:continue
            vals,total=direct(ds,F(w['mean']),bets,weights)
            self.assertEqual(list(map(F,w['components'])),vals);self.assertEqual(F(w['wealth']),total)
        if cert['status']=='bracket':
            self.assertGreater(F(cert['left_witness']['wealth']),threshold)
            self.assertLess(F(cert['right_witness']['wealth']),threshold)
            self.assertEqual(F(cert['left_witness']['mean']),lo);self.assertEqual(F(cert['right_witness']['mean']),hi)
        elif cert['status']=='exact':self.assertEqual(F(cert['left_witness']['wealth']),threshold)
        else:self.assertEqual(lo,F(-1));self.assertLess(F(cert['left_witness']['wealth']),threshold)
        for trial in cert['trials']:
            _,v=direct(ds,F(trial['mean']),bets,weights);self.assertEqual(F(trial['wealth']),v)
            self.assertEqual(trial['relation'],'above' if v>threshold else 'below' if v<threshold else 'equal')

    def test_exhaustive_products_and_brackets(self):
        bets=[F(1,4),F(1)];weights=[F(1,3),F(2,3)]
        for seq in product((-1,0,1),repeat=4):
            ds=list(seq);cs=confidence_sequence(ds,bets=bets,weights=weights,alpha='1/2',iterations=6)
            lows=[];ups=[]
            for t,row in enumerate(cs['trace'],1):
                self.check_certificate(ds[:t],row['certificate'],bets,weights,F(2),6)
                lows.append(F(row['certificate']['lower']));ups.append(F(row['certificate']['upper']))
                self.assertEqual(F(row['running_lower']),max(lows));self.assertEqual(F(row['running_upper']),max(ups))
                self.assertEqual(row['outer_interval'],[row['running_lower'],'1'])
    def test_candidate_matches_half_bet_original(self):
        ds=[1,-1,0,'1/2','-1/4',1]
        new=mean_evidence(ds,0,bets=[0,'1/2',1],weights=['1/3','1/3','1/3'])
        old=replay(ds,bets=[0,'1/4','1/2'],weights=['1/3','1/3','1/3'])
        self.assertEqual(new['final_wealth'],old['decisions']['mixture']['final_wealth'])
        self.assertEqual(new['running_max'],old['decisions']['mixture']['running_max'])
        self.assertEqual(new['first_crossing'],old['decisions']['mixture']['first_crossing'])
        for a,b in zip(new['trace'],old['trace']):self.assertEqual(a['components'],b['components'])
    def test_candidate_all_ternary_streams_means(self):
        for ds in product((-1,0,1),repeat=4):
            for m in (F(-1),F(-1,3),F(0),F(1,2),F(1)):
                x=mean_evidence(list(ds),m,bets=['1/3',1],weights=['1/4','3/4'],alpha='1/2')
                for t,row in enumerate(x['trace'],1):
                    vals,total=direct(ds[:t],m,[F(1,3),F(1)],[F(1,4),F(3,4)])
                    self.assertEqual(list(map(F,row['components'])),vals);self.assertEqual(F(row['wealth']),total)
                    self.assertTrue(all(F(f)>=0 for f in row['factors']))
    def test_equality_exact_root_and_closed_outer(self):
        x=confidence_sequence([1,1],bets=[1],alpha='1/4',iterations=4)
        cert=x['trace'][1]['certificate'];self.assertEqual(cert['status'],'exact');self.assertEqual(cert['lower'],'-1')
        x=confidence_sequence([1],bets=[1],alpha='2/3',iterations=4)
        self.assertEqual(x['trace'][0]['certificate']['lower'],'0');self.assertEqual(x['trace'][0]['certificate']['upper'],'0')
        self.assertEqual(x['trace'][0]['certificate']['status'],'exact');self.assertEqual(x['final_outer_interval'],['0','1'])
        self.assertEqual(mean_evidence([1],0,bets=[1],alpha='2/3')['first_crossing'],1)
    def test_no_rejection_and_degenerate(self):
        for ds,bets in (([],[1]),([-1]*8,[1]),([1]*8,[0])):
            self.assertEqual(confidence_sequence(ds,bets=bets)['final_outer_interval'],['-1','1'])
        x=mean_evidence([1,-1]*4,1,bets=[1]);self.assertLessEqual(F(x['running_max']),1)
        x=mean_evidence([-1,1],-1,bets=[1]);self.assertEqual(x['trace'][0]['wealth'],'1');self.assertEqual(x['trace'][1]['wealth'],'2')
    def test_reversal_retains_prefix_bound(self):
        x=confidence_sequence([1]*8+[-1]*12,bets=[1],alpha='1/4')
        self.assertEqual(x['final_outer_interval'],x['trace'][7]['outer_interval'])
        self.assertLess(F(x['trace'][-1]['certificate']['upper']),F(x['trace'][7]['running_lower']))
        self.assertTrue(all(F(a['running_lower'])<=F(b['running_lower']) for a,b in zip(x['trace'],x['trace'][1:])))
    def test_prefix_only_and_permutation_invariance(self):
        ds=[1,0,'1/2',-1,1,1]
        a=confidence_sequence(ds,bets=[1,'1/4'],weights=['2/3','1/3'])
        b=confidence_sequence(ds,bets=['1/4',1],weights=['1/3','2/3'])
        self.assertEqual(a['final_outer_interval'],b['final_outer_interval'])
        for i in range(len(ds)+1):self.assertEqual(confidence_sequence(ds[:i],bets=[1,'1/4'],weights=['2/3','1/3'])['trace'],a['trace'][:i])
    def test_refinement_nesting(self):
        ds=['1/2']*12
        a=confidence_sequence(ds,bets=[1],alpha='1/4',iterations=5)
        b=confidence_sequence(ds,bets=[1],alpha='1/4',iterations=12)
        for x,y in zip(a['trace'],b['trace']):
            self.assertLessEqual(F(x['running_lower']),F(y['running_lower']));self.assertGreaterEqual(F(x['running_upper']),F(y['running_upper']))
    def test_finite_law_coverage_and_every_conditional_witness(self):
        a=confidence_demo()['finite_coverage_audit'];mu=F(1,2)
        self.assertEqual(a['leaf_count'],256);self.assertEqual(F(a['crossing_probability']),F(a['exclusion_probability']))
        self.assertGreater(F(a['crossing_probability']),0);self.assertLessEqual(F(a['crossing_probability']),F(1,4))
        cross=F(0);miss=F(0);final=F(0);stopped=F(0)
        for leaf in a['leaves']:
            ds=list(map(F,leaf['differences']));mass=F(3,4)**ds.count(1)*F(1,4)**ds.count(-1)
            wealth=[direct(ds[:i],mu,[F(1)],[F(1)])[1] for i in range(1,9)]
            first=next((i for i,v in enumerate(wealth,1) if v>=4),None)
            self.assertEqual(leaf['first_crossing_at_true_mean'],first);self.assertEqual(F(leaf['mass']),mass)
            if first:cross+=mass
            if leaf['ever_excludes_true_mean']:miss+=mass
            final+=mass*wealth[-1];stopped+=mass*(wealth[first-1] if first else wealth[-1])
            self.assertFalse(leaf['ever_excludes_true_mean'] and not first)
        self.assertEqual(cross,F(a['crossing_probability']));self.assertEqual(miss,F(a['exclusion_probability']))
        self.assertEqual(final,1);self.assertEqual(stopped,1)
        for node in a['transformed_null_audit']['nodes']:
            self.assertEqual(node['conditional_mean'],'0');self.assertEqual(node['slack']['mixture'],'0')
    def test_full_capacity_no_mutation_or_rng(self):
        ds=[0]*64;bets=[F(i,15) for i in range(16)];snapshot=copy.deepcopy((ds,bets));state=random.getstate()
        x=confidence_sequence(ds,bets=bets,iterations=32)
        self.assertEqual(len(x['trace']),64);self.assertEqual((ds,bets),snapshot);self.assertEqual(random.getstate(),state)
        self.assertTrue(all(len(r['certificate']['left_witness']['components'])==16 for r in x['trace']))
    def test_invalid_exact_inputs_and_caps(self):
        for ds in ([1]*65,[True],[0.5],['nan'],[2],None):
            with self.assertRaises(ValueError):confidence_sequence(ds)
            with self.assertRaises(ValueError):mean_evidence(ds,0)
        for m in (True,0.5,'inf',2,-2):
            with self.assertRaises(ValueError):mean_evidence([1],m)
        for i in (True,0,33,1.5,'2'):
            with self.assertRaises(ValueError):confidence_sequence([1],iterations=i)
        for kw in ({'bets':[1,1]},{'bets':[2]},{'weights':['1/2']},{'alpha':1}):
            with self.assertRaises(ValueError):confidence_sequence([1],**kw)
    def test_cli_and_artifacts(self):
        for mode in ('mean','confidence','confidence-demo'):
            args=[] if mode.endswith('demo') else [str(ROOT/'examples'/f'{mode}-input.json')]
            p=subprocess.run([sys.executable,'-m','betlab',mode]+args,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr);x=json.loads(p.stdout)
            if mode=='confidence-demo':self.assertEqual(p.stdout,(ROOT/'examples/confidence-demo.json').read_text())
            elif mode=='mean':self.assertIn('first_crossing',x)
            else:self.assertIn('final_boundary_bracket',x)
    def test_cli_rejects_unknown_and_invalid_schema(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'in.json'
            cases=[('mean','{"schema_version":1,"differences":[1]}'),('confidence','{"schema_version":1,"differences":[1],"mean":0}'),('confidence','{"schema_version":1,"differences":[1],"iterations":true}'),('mean','{"schema_version":1,"differences":[1],"mean":0.1}'),('confidence','{"schema_version":1,"differences":[1],"alpha":NaN}'),('mean','{"schema_version":1,"schema_version":1,"differences":[1],"mean":0}')]
            for mode,text in cases:
                path.write_text(text);p=subprocess.run([sys.executable,'-m','betlab',mode,str(path)],cwd=ROOT,capture_output=True,text=True)
                self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,'');self.assertTrue(p.stderr.startswith('error:'))
