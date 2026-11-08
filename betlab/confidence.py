"""Conservative exact brackets for inversion of a fixed bounded-mean bet family."""
from fractions import Fraction as F
from .core import config, bounded, _json


def _data(differences):
    if not isinstance(differences, (list, tuple)) or len(differences) > 64:
        raise ValueError('confidence differences must contain 0..64 entries')
    return [bounded(d, -1, 1, 'difference') for d in differences]


def _wealth(ds, m, bs, ws):
    capital = []
    for b in bs:
        v = F(1)
        for d in ds:
            v *= 1+b*(d-m)/2
        capital.append(v)
    return {'mean': m, 'components': capital,
            'wealth': sum(w*v for w, v in zip(ws, capital))}


def mean_evidence(differences, mean, *, bets=None, weights=None, alpha='1/20'):
    """One fixed candidate null E[D_t|past]<=mean, not an observed sample mean."""
    ds = _data(differences)
    m = bounded(mean, -1, 1, 'mean')
    bs, ws, a = config(bets, weights, alpha)
    capital, trace, first, maximum = [F(1)]*len(bs), [], None, F(1)
    for t, d in enumerate(ds, 1):
        factors = [1+b*(d-m)/2 for b in bs]
        capital = [v*f for v, f in zip(capital, factors)]
        wealth = sum(w*v for w, v in zip(ws, capital))
        if first is None and wealth >= 1/a:
            first = t
        maximum = max(maximum, wealth)
        trace.append({'time': t, 'difference': d, 'factors': factors,
                      'components': capital[:], 'wealth': wealth})
    return _json({'schema_version': 1, 'mean': m, 'alpha': a, 'threshold': 1/a,
                  'bets': bs, 'effective_bets': [b/2 for b in bs], 'weights': ws,
                  'trace': trace, 'first_crossing': first, 'running_max': maximum,
                  'final_wealth': trace[-1]['wealth'] if trace else F(1),
                  'anytime_p_bound': min(F(1), 1/maximum),
                  'scope': 'one prespecified candidate conditional upper-mean null; no assumption inferred'})


def _bracket(ds, bs, ws, threshold, iterations):
    lo, hi = F(-1), F(1)
    left, right = _wealth(ds, lo, bs, ws), _wealth(ds, hi, bs, ws)
    trials = []
    if left['wealth'] < threshold:
        return {'status': 'no_rejection', 'lower': lo, 'upper': lo,
                'left_witness': left, 'right_witness': None, 'trials': trials}
    if left['wealth'] == threshold:
        return {'status': 'exact', 'lower': lo, 'upper': lo,
                'left_witness': left, 'right_witness': left, 'trials': trials}
    for _ in range(iterations):
        mid = (lo+hi)/2
        witness = _wealth(ds, mid, bs, ws)
        relation = ('equal' if witness['wealth'] == threshold else
                    'above' if witness['wealth'] > threshold else 'below')
        trials.append({'mean': mid, 'wealth': witness['wealth'], 'relation': relation})
        if relation == 'equal':
            return {'status': 'exact', 'lower': mid, 'upper': mid,
                    'left_witness': witness, 'right_witness': witness, 'trials': trials}
        if relation == 'above':
            lo, left = mid, witness
        else:
            hi, right = mid, witness
    assert left['wealth'] > threshold and right['wealth'] < threshold
    return {'status': 'bracket', 'lower': lo, 'upper': hi,
            'left_witness': left, 'right_witness': right, 'trials': trials}


def confidence_sequence(differences, *, bets=None, weights=None, alpha='1/20', iterations=16):
    """Closed outer intervals for one fixed conditional upper bound on every round."""
    if type(iterations) is not int or not 1 <= iterations <= 32:
        raise ValueError('iterations must be integer 1..32')
    ds = _data(differences)
    bs, ws, a = config(bets, weights, alpha)
    lower, upper, lp, up = F(-1), F(-1), 0, 0
    trace = []
    for t in range(1, len(ds)+1):
        cert = _bracket(ds[:t], bs, ws, 1/a, iterations)
        if cert['lower'] > lower:
            lower, lp = cert['lower'], t
        if cert['upper'] > upper:
            upper, up = cert['upper'], t
        assert lower <= upper and upper-lower <= F(2, 2**iterations)
        trace.append({'time': t, 'difference': ds[t-1], 'certificate': cert,
                      'running_lower': lower, 'running_upper': upper,
                      'lower_witness_prefix': lp, 'upper_witness_prefix': up,
                      'outer_interval': [lower, F(1)]})
    return _json({'schema_version': 1, 'alpha': a, 'threshold': 1/a,
                  'bets': bs, 'effective_bets': [b/2 for b in bs], 'weights': ws,
                  'iterations': iterations, 'maximum_boundary_uncertainty': F(2, 2**iterations),
                  'trace': trace, 'final_outer_interval': [lower, F(1)],
                  'final_boundary_bracket': [lower, upper],
                  'scope': 'simultaneous lower confidence bound for a fixed mu with E[D_t|past]<=mu at every round; closed conservative outer intervals; not a drifting mean estimate'})


def confidence_demo():
    from .tree import audit_tree
    from itertools import product
    # Exact law with mean 1/2: D=+1 with probability 3/4, -1 otherwise.
    def law(depth):
        if depth == 0:
            return None
        return {'outcomes': [
            {'probability': '3/4', 'difference': '1/4', 'next': law(depth-1)},
            {'probability': '1/4', 'difference': '-3/4', 'next': law(depth-1)}]}
    a, mu, depth = F(1, 4), F(1, 2), 8
    null = audit_tree(law(depth), bets=[1], alpha=a)
    leaves, excluded, crossings = [], F(0), F(0)
    for signs in product((-1, 1), repeat=depth):
        ds = list(signs)
        mass = F(3, 4)**ds.count(1)*F(1, 4)**ds.count(-1)
        cs = confidence_sequence(ds, bets=[1], alpha=a, iterations=8)
        ev = mean_evidence(ds, mu, bets=[1], alpha=a)
        miss = any(F(row['running_lower']) > mu for row in cs['trace'])
        crossed = ev['first_crossing'] is not None
        assert not miss or crossed
        if miss:
            excluded += mass
        if crossed:
            crossings += mass
        leaves.append({'differences': ds, 'mass': mass,
                       'final_outer_interval': cs['final_outer_interval'],
                       'final_boundary_bracket': cs['final_boundary_bracket'],
                       'first_crossing_at_true_mean': ev['first_crossing'],
                       'ever_excludes_true_mean': miss})
    assert crossings == F(null['summary']['mixture']['crossing_probability'])
    assert excluded <= crossings <= a
    return _json({'schema_version': 1,
                  'constant_positive': confidence_sequence(['1/2']*24, bets=[1], alpha='1/4'),
                  'reversal': confidence_sequence([1]*8+[-1]*12, bets=[1], alpha='1/4'),
                  'no_evidence': confidence_sequence([-1]*8, bets=[1], alpha='1/4'),
                  'finite_coverage_audit': {'true_mean': mu, 'positive_probability': F(3,4),
                      'depth': depth, 'alpha': a, 'leaf_count': len(leaves),
                      'exclusion_probability': excluded, 'crossing_probability': crossings,
                      'transformed_null_audit': null, 'leaves': leaves},
                  'scope': 'developed fixtures and exact supplied finite law; no real-model performance ranking'})
