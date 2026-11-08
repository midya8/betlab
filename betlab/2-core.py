"""Exact bounded-score betting. No data-generating assumptions are inferred."""
from fractions import Fraction
import re


def rational(value, name='value'):
    if isinstance(value, bool) or not isinstance(value, (str, int, Fraction)):
        raise ValueError(name + ' must be an exact integer, string or Fraction, not float/bool')
    if isinstance(value, str):
        if len(value) > 160 or not re.fullmatch(r'-?\d+(?:/\d+|\.\d+)?', value):
            raise ValueError(name + ' has invalid exact syntax')
    try:
        q = Fraction(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError(name + ' is not rational') from None
    if max(abs(q.numerator).bit_length(), q.denominator.bit_length()) > 512:
        raise ValueError(name + ' exceeds 512-bit input components')
    return q


def bounded(value, lo, hi, name):
    q = rational(value, name)
    if not lo <= q <= hi:
        raise ValueError(name + ' outside allowed range')
    return q


def config(bets=None, weights=None, alpha='1/20'):
    bets = ['0', '1/4', '1/2', '3/4', '1'] if bets is None else bets
    if not isinstance(bets, (list, tuple)) or not 1 <= len(bets) <= 16:
        raise ValueError('bets must have 1..16 entries')
    bs = [bounded(b, 0, 1, 'bet') for b in bets]
    if len(set(bs)) != len(bs):
        raise ValueError('bets must be distinct')
    if weights is None:
        ws = [Fraction(1, len(bs))] * len(bs)
    else:
        if not isinstance(weights, (list, tuple)) or len(weights) != len(bs):
            raise ValueError('weights must match bets')
        ws = [bounded(w, 0, 1, 'weight') for w in weights]
        if any(w <= 0 for w in ws) or sum(ws) != 1:
            raise ValueError('weights must be positive and sum exactly to one')
    a = bounded(alpha, 0, 1, 'alpha')
    if not 0 < a < 1:
        raise ValueError('alpha must lie strictly between zero and one')
    return bs, ws, a


def _states(ds, bs, ws):
    components = [Fraction(1)] * len(bs)
    plugin = Fraction(1)
    restart = Fraction(1)
    total = square = Fraction(0)
    states = []
    for i, d in enumerate(ds, 1):
        b = min(Fraction(1), max(Fraction(0), total / (1 + square)))
        old = plugin
        plugin *= 1 + b*d
        components = [v*(1+c*d) for v, c in zip(components, bs)]
        # Deliberately invalid comparator: external capital is injected at ruin.
        if restart == 0:
            restart = Fraction(1)
        restart *= 1+d
        states.append({'time': i, 'difference': d, 'past_sum': total,
                       'past_sum_squares': square, 'predictable_bet': b,
                       'predictable_previous': old, 'predictable_factor': 1+b*d,
                       'predictable': plugin, 'components': components[:],
                       'mixture': sum(w*v for w, v in zip(ws, components)),
                       'invalid_restart': restart})
        total += d
        square += d*d
    return states


def _json(x):
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _json(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)):
        return [_json(v) for v in x]
    return x


def replay(differences, *, bets=None, weights=None, alpha='1/20'):
    """One prespecified one-sided test, E[D_t|past] <= 0, D_t in [-1,1]."""
    bs, ws, a = config(bets, weights, alpha)
    if not isinstance(differences, (list, tuple)) or len(differences) > 256:
        raise ValueError('differences must contain 0..256 entries')
    ds = [bounded(d, -1, 1, 'difference') for d in differences]
    return _report(ds, bs, ws, a)


def _report(ds, bs, ws, a):
    states = _states(ds, bs, ws)
    decisions = {}
    for key in ('mixture', 'predictable', 'invalid_restart'):
        first = next((s['time'] for s in states if s[key] >= 1/a), None)
        maximum = max([Fraction(1)] + [s[key] for s in states])
        decisions[key] = {'first_crossing': first, 'crossed': first is not None,
                          'running_max': maximum,
                          'final_wealth': states[-1][key] if states else Fraction(1)}
        if key != 'invalid_restart':
            decisions[key]['anytime_p_bound'] = min(Fraction(1), 1/maximum)
    return _json({'schema_version': 1, 'null': 'E[difference_t | past] <= 0',
                  'alpha': a, 'threshold': 1/a, 'bets': bs, 'weights': ws,
                  'observations': len(ds), 'trace': states, 'decisions': decisions,
                  'scope': 'one prespecified stream/test; assumptions not verified from a sequence',
                  'invalid_restart_is_not_an_e_process': True})


def paired(baseline, candidate, **kwargs):
    if not isinstance(baseline, (list, tuple)) or not isinstance(candidate, (list, tuple)):
        raise ValueError('paired scores must be sequences')
    if len(baseline) != len(candidate) or len(baseline) > 256:
        raise ValueError('paired scores must have equal length <=256')
    ds = [bounded(c, 0, 1, 'candidate')-bounded(b, 0, 1, 'baseline')
          for b, c in zip(baseline, candidate)]
    # Internal differences are exact arithmetic, not reparsed bounded input strings.
    bs, ws, a = config(**kwargs)
    return _report(ds, bs, ws, a)
