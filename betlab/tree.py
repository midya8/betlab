"""Exhaustive finite-law audit, not verification of a real data source."""
from fractions import Fraction
from .core import config, bounded, _states, _json


def audit_tree(tree, *, bets=None, weights=None, alpha='1/20'):
    bs, ws, a = config(bets, weights, alpha)
    nodes, leaves, seen = [], [], set()

    def wealth(ds):
        if not ds:
            return {'mixture': Fraction(1), 'predictable': Fraction(1),
                    'invalid_restart': Fraction(1)}
        return _states(ds, bs, ws)[-1]

    def walk(node, ds, mass, first, stopped, path):
        current = wealth(ds)
        first, stopped = dict(first), dict(stopped)
        for key in current_keys:
            if first[key] is None and current[key] >= 1/a:
                first[key], stopped[key] = len(ds), current[key]
        if node is None:
            if len(leaves) >= 256:
                raise ValueError('tree exceeds 256 leaves')
            leaves.append({'path': path, 'mass': mass, 'differences': ds[:],
                           'wealth': {k: current[k] for k in current_keys},
                           'first_crossing': first,
                           'stopped_wealth': {k: current[k] if stopped[k] is None else stopped[k]
                                              for k in current_keys}})
            return
        if not isinstance(node, dict) or set(node) != {'outcomes'}:
            raise ValueError('node must be null or exactly {outcomes: ...}')
        if id(node) in seen:
            raise ValueError('tree contains alias or cycle')
        seen.add(id(node))
        if len(nodes) >= 255 or len(ds) >= 8:
            raise ValueError('tree exceeds 255 internal nodes or depth eight')
        outs = node['outcomes']
        if not isinstance(outs, list) or not 1 <= len(outs) <= 4:
            raise ValueError('each internal node needs 1..4 outcomes')
        parsed = []
        for out in outs:
            if not isinstance(out, dict) or set(out) != {'probability', 'difference', 'next'}:
                raise ValueError('outcome schema mismatch')
            p = bounded(out['probability'], 0, 1, 'probability')
            if p == 0:
                raise ValueError('zero probability branches must be omitted')
            d = bounded(out['difference'], -1, 1, 'difference')
            parsed.append((p, d, out['next']))
        if sum(p for p, _, _ in parsed) != 1:
            raise ValueError('branch probabilities must sum exactly to one')
        mean = sum(p*d for p, d, _ in parsed)
        if mean > 0:
            raise ValueError('conditional null fails at path ' + str(path))
        child_expectations = {k: sum(p*wealth(ds+[d])[k] for p, d, _ in parsed)
                              for k in current_keys}
        row = {'path': path, 'mass': mass, 'conditional_mean': mean,
               'current': {k: current[k] for k in current_keys},
               'next_expectation': child_expectations,
               'slack': {k: current[k]-child_expectations[k] for k in current_keys}}
        assert row['slack']['mixture'] >= 0 and row['slack']['predictable'] >= 0
        nodes.append(row)
        for j, (p, d, nxt) in enumerate(parsed):
            walk(nxt, ds+[d], mass*p, first, stopped, path+[j])

    current_keys = ('mixture', 'predictable', 'invalid_restart')
    walk(tree, [], Fraction(1), dict.fromkeys(current_keys), dict.fromkeys(current_keys), [])
    assert sum(l['mass'] for l in leaves) == 1
    summaries = {}
    for k in current_keys:
        cross = sum(l['mass'] for l in leaves if l['first_crossing'][k] is not None)
        final = sum(l['mass']*l['wealth'][k] for l in leaves)
        stop = sum(l['mass']*l['stopped_wealth'][k] for l in leaves)
        summaries[k] = {'crossing_probability': cross, 'expected_final_wealth': final,
                        'expected_stopped_wealth': stop, 'within_alpha': cross <= a}
        if k != 'invalid_restart':
            assert cross <= a and final <= 1 and stop <= 1
    return _json({'schema_version': 1, 'alpha': a, 'threshold': 1/a,
                  'bets': bs, 'weights': ws, 'internal_nodes': len(nodes),
                  'leaf_count': len(leaves), 'nodes': nodes, 'leaves': leaves,
                  'summary': summaries,
                  'scope': 'exact supplied finite null tree only; no inference of real-world null'})


def coin_tree(depth, probability='1/2'):
    if isinstance(depth, bool) or not isinstance(depth, int) or not 0 <= depth <= 8:
        raise ValueError('depth must be integer 0..8')
    p = bounded(probability, 0, Fraction(1, 2), 'probability')
    if depth == 0:
        return None
    outcomes = []
    for prob, d in ((p, 1), (1-p, -1)):
        if prob:
            outcomes.append({'probability': str(prob), 'difference': d,
                             'next': coin_tree(depth-1, p)})
    return {'outcomes': outcomes}
