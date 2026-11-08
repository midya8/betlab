import copy
from fractions import Fraction as F
import itertools
import random
import unittest
from betlab import replay, paired
from betlab.core import rational


class ReplayTests(unittest.TestCase):
    def test_empty(self):
        x = replay([])
        self.assertEqual(x['trace'], [])
        for k in ('mixture','predictable'):
            self.assertEqual(x['decisions'][k]['anytime_p_bound'], '1')
    def test_hand_computation(self):
        x = replay([1,-1,1], bets=['1/2'], alpha='1/2')
        self.assertEqual([r['mixture'] for r in x['trace']], ['3/2','3/4','9/8'])
        self.assertEqual(x['trace'][1]['predictable_bet'], '1/2')
        self.assertEqual(x['trace'][2]['predictable_bet'], '0')
    def test_mixture_is_average_not_max(self):
        x = replay([1,1], bets=[0,1], weights=['3/4','1/4'], alpha='1/2')
        self.assertEqual(x['trace'][-1]['components'], ['1','4'])
        self.assertEqual(x['trace'][-1]['mixture'],'7/4')
        self.assertFalse(x['decisions']['mixture']['crossed'])
    def test_equality_crossing_and_absorption(self):
        x = replay([1,1,-1,1], bets=[1], alpha='1/4')
        self.assertEqual(x['decisions']['mixture']['first_crossing'],2)
        self.assertEqual(x['decisions']['mixture']['final_wealth'],'0')
        self.assertEqual(x['trace'][-1]['mixture'],'0')
        self.assertEqual(x['trace'][-1]['invalid_restart'],'2')
    def test_running_p_monotone(self):
        ds=[1,1,1,-1,-1,1]
        ps=[F(replay(ds[:n])['decisions']['mixture']['anytime_p_bound']) for n in range(7)]
        self.assertEqual(ps,sorted(ps,reverse=True))
    def test_prefix_predictability(self):
        a=replay(['1/2','-1/4',1,1])['trace']
        b=replay(['1/2','-1/4',-1,-1])['trace']
        self.assertEqual(a[:2],b[:2])
        self.assertEqual(a[2]['predictable_bet'],b[2]['predictable_bet'])
    def test_exhaustive_product_reference(self):
        for ds in itertools.product((-1,0,1),repeat=5):
            rows=replay(list(ds))['trace']
            for t,row in enumerate(rows,1):
                capitals=[F(1)]*5
                for d in ds[:t]:
                    capitals=[c*(1+b*d) for c,b in zip(capitals,map(F,('0','1/4','1/2','3/4','1')))]
                self.assertEqual(list(map(F,row['components'])),capitals)
                self.assertEqual(F(row['mixture']),sum(capitals)/5)
    def test_predictable_independent_reference(self):
        rng=random.Random(93)
        for _ in range(30):
            ds=[F(rng.randint(-4,4),4) for _ in range(20)]
            rows=replay(ds)['trace']; k=F(1)
            for t,d in enumerate(ds):
                b=min(F(1),max(F(0),sum(ds[:t])/(1+sum(x*x for x in ds[:t]))))
                k*=1+b*d
                self.assertEqual(F(rows[t]['predictable_bet']),b)
                self.assertEqual(F(rows[t]['predictable']),k)
    def test_paired(self):
        self.assertEqual(paired(['0.1',1],['0.3',0]),replay(['1/5',-1]))
    def test_internal_difference_not_input_capped(self):
        a=F(1,2**511-1);b=F(1,2**510-1)
        self.assertEqual(F(paired([a],[b])['trace'][0]['difference']),b-a)
    def test_capacity(self):
        self.assertEqual(replay([0]*256,bets=[F(i,15) for i in range(16)])['observations'],256)
    def test_no_mutation_rng(self):
        ds=[1,0,-1];before=copy.deepcopy(ds);state=random.getstate();replay(ds)
        self.assertEqual(ds,before);self.assertEqual(random.getstate(),state)
    def test_exact_decimals(self):
        self.assertEqual(rational('0.10'),F(1,10))
        self.assertEqual(rational('-2/4'),F(-1,2))
    def test_invalid_numbers(self):
        for v in (True,False,0.5,float('nan'),'nan','inf','1/0',' 1','1e2','1.' ,'1'*161,2**513):
            with self.subTest(v=str(v)),self.assertRaises(ValueError):replay([v])
    def test_config_errors(self):
        for kw in ({'alpha':0},{'alpha':1},{'alpha':True},{'bets':[]},{'bets':[1,1]},
                   {'bets':[-1]},{'bets':[2]},{'weights':[1]}, {'weights':[0]*5},
                   {'weights':['1/4']*5},{'bets':list(range(17))}):
            with self.subTest(kw=kw),self.assertRaises(ValueError):replay([],**kw)
    def test_sequence_errors(self):
        for ds in (None,'1',{},[1]*257,[-2],[2]):
            with self.assertRaises(ValueError):replay(ds)
        for a,b in (([],[1]),([2],[1]),([0],[-1]),('a','b')):
            with self.assertRaises(ValueError):paired(a,b)
