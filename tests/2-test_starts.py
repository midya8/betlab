import copy
from fractions import Fraction as F
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from betlab import start_mixture, audit_starts, coin_tree, replay, starts_demo
ROOT=Path(__file__).resolve().parents[1]


class StartTests(unittest.TestCase):
    def test_single_start_matches_original(self):
        ds=[1,-1,'1/2','-1/4',0,1]
        for bets in ([1],['0','1/4','1/2','3/4','1']):
            old=replay(ds,bets=bets,alpha='1/4');new=start_mixture(ds,[1],bets=bets,alpha='1/4')
            self.assertEqual(new['decision'],old['decisions']['mixture'])
            for a,b in zip(new['trace'],old['trace']):self.assertEqual(a['wealth'],b['mixture'])
    def test_every_short_sequence_product_reference(self):
        starts=[1,2,4];ws=[F(1,2),F(1,3),F(1,6)];bets=[F(1,4),F(3,4)];bw=[F(1,3),F(2,3)]
        for ds in itertools.product((-1,0,1),repeat=5):
            x=start_mixture(list(ds),starts,start_weights=ws,bets=bets,weights=bw)
            for t,row in enumerate(x['trace'],1):
                expected=F(0)
                for start,w,c in zip(starts,ws,row['components']):
                    vals=[]
                    for b in bets:
                        v=F(1)
                        for d in ds[start-1:t] if t>=start else ():v*=1+b*d
                        vals.append(v)
                    self.assertEqual(list(map(F,c['bet_wealth'])),vals)
                    local=sum(a*b for a,b in zip(bw,vals));expected+=w*local
                    self.assertEqual(F(c['local_mixture']),local)
                    self.assertEqual(F(c['contribution']),w*local)
                self.assertEqual(F(row['wealth']),expected)
                self.assertEqual(F(row['started_budget'])+F(row['unstarted_budget']),1)
    def test_future_only_is_constant_one(self):
        x=start_mixture([1]*8,[9,256],bets=[1])
        self.assertEqual(x['decision']['final_wealth'],'1');self.assertFalse(x['decision']['crossed'])
        self.assertTrue(all(r['wealth']=='1' and r['unstarted_budget']=='1' for r in x['trace']))
        a=audit_starts(coin_tree(3),[9],bets=[1])['scheduled_audit']
        self.assertEqual(a['summary']['crossing_probability'],'0')
        self.assertTrue(all(n['slack']=='0' for n in a['nodes']))
    def test_delayed_signal_and_permanent_ruin(self):
        x=starts_demo()['delayed_signal'];self.assertEqual(x['decision']['first_crossing'],12)
        self.assertEqual(x['decision']['final_wealth'],'0')
        self.assertTrue(all(r['components'][0]['bet_wealth']==['0'] for r in x['trace']))
        row=x['trace'][15];self.assertEqual(row['wealth'],'257/3');self.assertEqual(row['unstarted_budget'],'1/3')
        self.assertTrue(x['decision']['crossed'])
    def test_equality_threshold(self):
        x=start_mixture([1,1],[1],bets=[1],alpha='1/4');self.assertEqual(x['decision']['first_crossing'],2)
    def test_empty(self):
        x=start_mixture([],[1]);self.assertEqual(x['trace'],[]);self.assertEqual(x['decision']['final_wealth'],'1')
        a=audit_starts(None,[1]);self.assertEqual(a['scheduled_audit']['summary']['expected_stopped_wealth'],'1')
    def test_unsorted_schedule_preserves_weight_pairs(self):
        a=start_mixture([1,-1,1,1],[4,1,2],start_weights=['1/6','1/2','1/3'])
        b=start_mixture([1,-1,1,1],[1,2,4],start_weights=['1/2','1/3','1/6'])
        self.assertEqual(a,b)
    def test_fair_tree_independent_paths_and_slacks(self):
        x=audit_starts(coin_tree(8),[1,3,5,9],bets=[1],alpha='1/4')
        a=x['scheduled_audit'];self.assertEqual(a['summary']['crossing_probability'],'5/32')
        self.assertEqual(a['summary']['expected_final_wealth'],'1');self.assertEqual(a['summary']['expected_stopped_wealth'],'1')
        # Reconstruct from direct suffix products, not replay/start implementation.
        cross=F(0);final=F(0);stopped=F(0)
        def wealth(ds):
            total=F(0)
            for start in (1,3,5,9):
                v=F(1)
                for d in ds[start-1:] if len(ds)>=start else ():v*=1+d
                total+=v/4
            return total
        for ds in itertools.product((-1,1),repeat=8):
            vals=[wealth(ds[:t]) for t in range(1,9)];hit=next((v for v in vals if v>=4),None)
            cross+=F(hit is not None,256);final+=vals[-1]/256;stopped+=(vals[-1] if hit is None else hit)/256
        self.assertEqual(F(a['summary']['crossing_probability']),cross)
        self.assertEqual(F(a['summary']['expected_final_wealth']),final)
        self.assertEqual(F(a['summary']['expected_stopped_wealth']),stopped)
        bypath={tuple(n['path']):F(n['current']) for n in a['nodes']}
        bypath.update({tuple(l['path']):F(l['final_wealth']) for l in a['leaves']})
        for n in a['nodes']:
            p=tuple(n['path']);expected=(bypath[p+(0,)]+bypath[p+(1,)])/2
            self.assertEqual(F(n['next_expectation']),expected)
            self.assertEqual(F(n['slack']),bypath[p]-expected)
    def test_negative_tree_and_base_parity(self):
        t=coin_tree(6,'1/3');x=audit_starts(t,[1,3,5,9],bets=[1],alpha='1/4')
        self.assertEqual(x['scheduled_audit']['summary']['crossing_probability'],'17/729')
        self.assertTrue(all(F(n['slack'])>=0 for n in x['scheduled_audit']['nodes']))
        from betlab import audit_tree
        self.assertEqual(x['base_audit'],audit_tree(t,bets=[1],alpha='1/4'))
    def test_variable_depth_multibranch_and_invalid_law(self):
        t={'outcomes':[{'probability':'1/4','difference':d,'next':coin_tree(i)} for i,d in enumerate((1,0,-1,-1))]}
        x=audit_starts(t,[1,2,4,9],alpha='1/4');self.assertEqual(len(x['scheduled_audit']['leaves']),15)
        self.assertEqual(sum(F(l['mass']) for l in x['scheduled_audit']['leaves']),1)
        t['outcomes'][0]['difference']=2
        with self.assertRaises(ValueError):audit_starts(t,[1])
    def test_maximum_dimensions_and_no_mutation(self):
        ds=[0]*256;starts=list(range(1,17));bets=[F(i,15) for i in range(16)];before=copy.deepcopy((ds,starts,bets));rng=random.getstate()
        x=start_mixture(ds,starts,bets=bets)
        self.assertEqual(x['decision']['final_wealth'],'1');self.assertEqual(len(x['trace'][-1]['components']),16)
        self.assertEqual((ds,starts,bets),before);self.assertEqual(random.getstate(),rng)
    def test_bad_schedule_and_inputs(self):
        for starts,sw in (([],None),([True],None),([0],None),([257],None),([1,1],None),('1',None),
                          (list(range(1,18)),None),([1],[0]),([1,2],[1]),([1,2],['1/4','1/2']),([1,2],[0,1])):
            with self.assertRaises(ValueError):start_mixture([] ,starts,start_weights=sw)
        for ds in ([True],[0.5],[-2],[1]*257,None):
            with self.assertRaises(ValueError):start_mixture(ds,[1])
    def test_cli_three_new_modes_and_old_demo_unchanged(self):
        for mode in ('starts-demo','starts','starts-tree'):
            args=[sys.executable,'-m','betlab',mode]
            if mode!='starts-demo':args.append(str(ROOT/'examples'/f'{mode}-input.json'))
            p=subprocess.run(args,cwd=ROOT,capture_output=True);self.assertEqual(p.returncode,0,p.stderr)
            expected=starts_demo() if mode=='starts-demo' else None
            if expected is not None:self.assertEqual(json.loads(p.stdout),expected)
        p=subprocess.run([sys.executable,'-m','betlab','demo'],cwd=ROOT,capture_output=True)
        self.assertEqual(p.stdout,(ROOT/'examples/demo.json').read_bytes())
    def test_cli_schedule_schema_errors(self):
        samples=[{'schema_version':1,'differences':[]},
                 {'schema_version':1,'differences':[],'starts':[1],'start_weights':[0]},
                 {'schema_version':1,'differences':[],'starts':[1],'surprise':1}]
        for x in samples:
            with tempfile.NamedTemporaryFile() as f:
                f.write(json.dumps(x).encode());f.flush();p=subprocess.run([sys.executable,'-m','betlab','starts',f.name],cwd=ROOT,capture_output=True)
            self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'')
