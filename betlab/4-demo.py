from fractions import Fraction
from .core import replay, paired
from .tree import audit_tree, coin_tree


def _summary(x):
    return {k: x[k] for k in ('schema_version','alpha','threshold','bets','weights',
                              'internal_nodes','leaf_count','summary','scope')} | {
        'root_witness': x['nodes'][0],
        'first_restart_violation': next(n for n in x['nodes']
                                        if Fraction(n['slack']['invalid_restart']) < 0)}


def demo():
    improved = paired(['1/2']*32, ['3/4']*32)
    reversal = replay([1]*8+[-1]*12, alpha='1/4')
    null_tree = audit_tree(coin_tree(8), alpha='1/4')
    conservative_tree = audit_tree(coin_tree(6, '1/3'), alpha='1/4')
    assert improved['decisions']['mixture']['first_crossing'] == 19
    assert improved['decisions']['predictable']['first_crossing'] == 17
    assert reversal['decisions']['mixture']['crossed']
    assert Fraction(reversal['decisions']['mixture']['final_wealth']) < 4
    assert null_tree['summary']['invalid_restart']['crossing_probability'] == '201/256'
    assert null_tree['summary']['mixture']['crossing_probability'] == '5/64'
    assert null_tree['summary']['predictable']['crossing_probability'] == '9/128'
    return {'schema_version': 1, 'paired_improvement': improved,
            'cross_then_reverse': reversal, 'fair_coin_audit': _summary(null_tree),
            'negative_drift_audit': _summary(conservative_tree),
            'development_fixture': True, 'not_a_model_benchmark': True}
