import copy
from fractions import Fraction as F
import itertools
import random
import unittest
from betlab import audit_tree, coin_tree, replay


class TreeTests(unittest.TestCase):
    def test_fair_tree_and_restart_failure(self):
        x=audit_tree(coin_tree(8),bets=[1],alpha='1/4')
        self.assertEqual((x['internal_nodes'],x['leaf_count']),(255,256))
        self.assertEqual(x['summary']['mixture']['crossing_probability'],'1/4')
        self.assertEqual(x['summary']['mixture']['expected_final_wealth'],'1')
        self.assertEqual(x['summary']['mixture']['expected_stopped_wealth'],'1')
        self.assertEqual(x['summary']['invalid_restart']['crossing_probability'],'201/256')
        self.assertFalse(x['summary']['invalid_restart']['within_alpha'])
        self.assertTrue(any(F(n['slack']['invalid_restart'])<0 for n in x['nodes']))
    def test_independent_path_enumeration(self):
        x=audit_tree(coin_tree(6),alpha='1/4')
        expected=F(0);cross=F(0)
        for ds in itertools.product((-1,1),repeat=6):
            r=replay(list(ds),alpha='1/4')['decisions']['mixture']
            expected+=F(r['final_wealth'])/64
            cross+=F(r['crossed'])/64
        self.assertEqual(F(x['summary']['mixture']['crossing_probability']),cross)
        self.assertEqual(F(x['summary']['mixture']['expected_final_wealth']),expected)
    def test_negative_drift_slacks(self):
        x=audit_tree(coin_tree(5,'1/3'))
        self.assertLess(F(x['summary']['mixture']['expected_final_wealth']),1)
        for n in x['nodes']:
            self.assertEqual(n['conditional_mean'],'-1/3')
            for k in ('mixture','predictable'):
                self.assertGreaterEqual(F(n['slack'][k]),0)
    def test_variable_depth_general_outcomes(self):
        tree={'outcomes':[{'probability':'1/2','difference':'1/2','next':None},
                          {'probability':'1/2','difference':'-3/4','next':coin_tree(2)}]}
        x=audit_tree(tree)
        self.assertEqual(x['leaf_count'],5)
        self.assertEqual(x['nodes'][0]['conditional_mean'],'-1/8')
        self.assertEqual(sum(F(l['mass']) for l in x['leaves']),1)
    def test_null_node(self):
        x=audit_tree(None);self.assertEqual(x['leaf_count'],1)
        self.assertEqual(x['summary']['mixture']['expected_stopped_wealth'],'1')
    def test_zero_outcome(self):
        x=audit_tree({'outcomes':[{'probability':1,'difference':0,'next':None}]})
        self.assertEqual(x['summary']['mixture']['expected_final_wealth'],'1')
    def test_conditional_not_marginal_null(self):
        # Marginal drift at round two is zero, conditional means have opposite signs.
        bad={'outcomes':[{'probability':'1/2','difference':1,'next':
             {'outcomes':[{'probability':1,'difference':1,'next':None}]}},
             {'probability':'1/2','difference':-1,'next':
             {'outcomes':[{'probability':1,'difference':-1,'next':None}]}}]}
        with self.assertRaisesRegex(ValueError,'conditional null'):audit_tree(bad)
    def test_schemas_and_laws(self):
        for t in ({},{'outcomes':[]},{'outcomes':[{}]}, {'outcomes':[{'probability':0,'difference':0,'next':None}]},
                  {'outcomes':[{'probability':'1/2','difference':0,'next':None}]},
                  {'outcomes':[{'probability':1,'difference':1,'next':None}]},
                  {'outcomes':[{'probability':1,'difference':-2,'next':None}]}):
            with self.assertRaises(ValueError):audit_tree(t)
    def test_alias_cycle_and_depth(self):
        t=coin_tree(1);t['outcomes'][0]['next']=t
        with self.assertRaises(ValueError):audit_tree(t)
        t=coin_tree(1);t['outcomes'][0]['next']=coin_tree(8)
        with self.assertRaises(ValueError):audit_tree(t)
        shared=coin_tree(1);t=coin_tree(1)
        for o in t['outcomes']:o['next']=shared
        with self.assertRaises(ValueError):audit_tree(t)
    def test_coin_guards(self):
        for n,p in ((True,'1/2'),(9,'1/2'),(-1,'1/2'),(2,'3/4'),(2,0.5)):
            with self.assertRaises(ValueError):coin_tree(n,p)
        self.assertEqual(audit_tree(coin_tree(8,0))['leaf_count'],1)
    def test_no_mutation(self):
        t=coin_tree(3);before=copy.deepcopy(t);state=random.getstate();audit_tree(t)
        self.assertEqual(t,before);self.assertEqual(random.getstate(),state)
