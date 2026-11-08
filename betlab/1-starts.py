"""Prespecified finite start-time mixtures. One initial capital, never free refills."""
from fractions import Fraction
from .core import bounded, config, _json
from .tree import audit_tree, coin_tree


def _schedule(starts, start_weights):
    if not isinstance(starts, (list, tuple)) or not 1 <= len(starts) <= 16:
        raise ValueError('starts must contain 1..16 distinct integer times')
    if any(type(t) is not int or not 1 <= t <= 256 for t in starts) or len(set(starts)) != len(starts):
        raise ValueError('start times must be distinct integers in 1..256')
    if start_weights is None:
        ws = [Fraction(1, len(starts))]*len(starts)
    else:
        if not isinstance(start_weights, (list, tuple)) or len(start_weights) != len(starts):
            raise ValueError('start_weights must match starts')
        ws = [bounded(w, 0, 1, 'start weight') for w in start_weights]
        if any(w <= 0 for w in ws) or sum(ws) != 1:
            raise ValueError('start weights must be positive and sum exactly to one')
    # Sort paired starts/weights for canonical output, without changing allocation.
    return tuple(zip(*sorted(zip(starts, ws))))


def _trace(ds, starts, sw, bs, bw):
    capitals = [[Fraction(1)]*len(bs) for _ in starts]
    rows = []
    for t, d in enumerate(ds, 1):
        components = []
        for i, (start, budget) in enumerate(zip(starts, sw)):
            if t >= start:
                capitals[i] = [v*(1+b*d) for v, b in zip(capitals[i], bs)]
            local = sum(w*v for w, v in zip(bw, capitals[i]))
            components.append({'start': start, 'weight': budget, 'active': t >= start,
                               'bet_wealth': capitals[i][:], 'local_mixture': local,
                               'contribution': budget*local})
        reserve = sum((w for start, w in zip(starts, sw) if start > t), Fraction(0))
        rows.append({'time': t, 'difference': d, 'components': components,
                     'unstarted_budget': reserve, 'started_budget': 1-reserve,
                     'wealth': sum(c['contribution'] for c in components)})
    return rows


def start_mixture(differences, starts, *, start_weights=None, bets=None, weights=None, alpha='1/20'):
    """A fixed convex mixture of start/bet processes, each equal to one before start."""
    ss, sw = _schedule(starts, start_weights)
    bs, bw, a = config(bets, weights, alpha)
    if not isinstance(differences, (list, tuple)) or len(differences) > 256:
        raise ValueError('differences must contain 0..256 entries')
    ds = [bounded(d, -1, 1, 'difference') for d in differences]
    rows = _trace(ds, ss, sw, bs, bw)
    first = next((r['time'] for r in rows if r['wealth'] >= 1/a), None)
    maximum = max([Fraction(1)]+[r['wealth'] for r in rows])
    return _json({'schema_version': 1, 'null': 'E[difference_t | past] <= 0',
                  'starts': ss, 'start_weights': sw, 'bets': bs, 'weights': bw,
                  'alpha': a, 'threshold': 1/a, 'initial_wealth': Fraction(1),
                  'observations': len(ds), 'trace': rows,
                  'decision': {'first_crossing': first, 'crossed': first is not None,
                               'final_wealth': rows[-1]['wealth'] if rows else Fraction(1),
                               'running_max': maximum, 'anytime_p_bound': min(Fraction(1), 1/maximum)},
                  'scope': 'one finite prespecified schedule and test; no data-dependent starts or free refills'})


def audit_starts(tree, starts, *, start_weights=None, bets=None, weights=None, alpha='1/20'):
    """Exact scheduled-mixture node/leaf audit, with unchanged original audit nested."""
    ss, sw = _schedule(starts, start_weights)
    bs, bw, a = config(bets, weights, alpha)
    base = audit_tree(tree, bets=bets, weights=weights, alpha=alpha)
    histories = {(): []}
    masses = {(): Fraction(1)}
    for leaf in base['leaves']:
        path, ds = leaf['path'], list(map(Fraction, leaf['differences']))
        for t in range(1, len(path)+1):
            histories[tuple(path[:t])] = ds[:t]
        masses[tuple(path)] = Fraction(leaf['mass'])
    for node in base['nodes']:
        masses[tuple(node['path'])] = Fraction(node['mass'])

    def value(ds):
        if not ds:
            return Fraction(1)
        return _trace(ds, ss, sw, bs, bw)[-1]['wealth']

    nodes = []
    for node in base['nodes']:
        p = tuple(node['path'])
        current = value(histories[p])
        children = sorted(k for k in masses if len(k) == len(p)+1 and k[:-1] == p)
        expected = sum(masses[c]/masses[p]*value(histories[c]) for c in children)
        assert children and expected <= current
        reserve = sum((w for t, w in zip(ss, sw) if t > len(p)), Fraction(0))
        nodes.append({'path': list(p), 'mass': masses[p], 'current': current,
                      'unstarted_budget': reserve, 'next_expectation': expected,
                      'slack': current-expected})
    leaves = []
    for leaf in base['leaves']:
        ds = histories[tuple(leaf['path'])]
        rows = _trace(ds, ss, sw, bs, bw)
        first_row = next((r for r in rows if r['wealth'] >= 1/a), None)
        final = rows[-1]['wealth'] if rows else Fraction(1)
        leaves.append({'path': leaf['path'], 'mass': Fraction(leaf['mass']),
                       'final_wealth': final, 'first_crossing': first_row['time'] if first_row else None,
                       'stopped_wealth': first_row['wealth'] if first_row else final})
    cross = sum((l['mass'] for l in leaves if l['first_crossing'] is not None), Fraction(0))
    final = sum(l['mass']*l['final_wealth'] for l in leaves)
    stop = sum(l['mass']*l['stopped_wealth'] for l in leaves)
    assert cross <= a and final <= 1 and stop <= 1
    return _json({'schema_version': 1, 'starts': ss, 'start_weights': sw,
                  'bets': bs, 'weights': bw, 'alpha': a, 'threshold': 1/a,
                  'base_audit': base, 'scheduled_audit': {
                      'nodes': nodes, 'leaves': leaves,
                      'summary': {'crossing_probability': cross, 'expected_final_wealth': final,
                                  'expected_stopped_wealth': stop, 'within_alpha': cross <= a}},
                  'scope': 'exact supplied finite null tree and prespecified schedule only'})


def starts_demo():
    from .core import replay
    ds = [-1]*8+[1]*8+[-1]*8
    replayed = start_mixture(ds, [1, 9, 17], bets=[1], alpha='1/4')
    baseline = replay(ds, bets=[1], alpha='1/4')
    law = audit_starts(coin_tree(8), [1, 3, 5, 9], bets=[1], alpha='1/4')
    neg = audit_starts(coin_tree(6, '1/3'), [1, 3, 5, 9], bets=[1], alpha='1/4')
    assert replayed['decision']['first_crossing'] == 12
    assert replayed['decision']['final_wealth'] == '0'
    assert not baseline['decisions']['mixture']['crossed']
    def compact(audit):
        return {'summary': audit['scheduled_audit']['summary'],
                'internal_nodes': len(audit['scheduled_audit']['nodes']),
                'leaf_count': len(audit['scheduled_audit']['leaves']),
                'root_witness': audit['scheduled_audit']['nodes'][0],
                'reserved_weight': '1/4',
                'invalid_free_restart_summary': audit['base_audit']['summary']['invalid_restart']}
    return {'schema_version': 1, 'delayed_signal': replayed,
            'from_start_control': baseline, 'fair_null': compact(law),
            'negative_drift_null': compact(neg),
            'development_fixture': True, 'not_a_power_ranking': True}
