"""Certified rational brackets; only display coordinates use floats."""
import base64
from fractions import Fraction as F
import html
import json
from pathlib import Path
import sys
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from betlab import confidence_demo


def render(r):
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="1200" viewBox="0 0 1120 1200">',
         '<rect width="1120" height="1200" fill="#f4f1ed"/><rect x="16" y="16" width="1088" height="1168" rx="18" fill="white"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#292929}.muted{fill:#666}</style>']
    def text(x,y,s,size=17,extra=''):
        out.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{html.escape(str(s))}</text>')
    def cell(id,x,y,s):text(x,y,s,18,f'id="cell-{id}" data-value="{s}"')
    text(42,58,'BetLab / confidence endpoints with rational certificates',27,'font-weight="700"')
    text(42,88,'Fixed factors 1 + b*(D-m)/2. Bet b=1, alpha=1/4; conservative closed outer intervals [L,1].',17,'class="muted"')
    def panel(key,title,subtitle,y0):
        x=r[key];rows=x['trace'];n=len(rows)
        text(42,y0,title,21,'font-weight="700"');text(42,y0+28,subtitle,16,'class="muted"')
        def xy(t,v):return 94+930*t/n,y0+235-80*(1+float(F(v)))
        for v in (-1,0,1):
            _,y=xy(0,v);out.append(f'<line x1="94" y1="{y:.3f}" x2="1024" y2="{y:.3f}" stroke="#ddd"/>');text(56,y+5,v,14)
        curves={key+'-running':['-1']+[a['running_lower'] for a in rows],
                key+'-current':['-1']+[a['certificate']['lower'] for a in rows]}
        for k,c in ((key+'-current','#c27a31'),(key+'-running','#127e71')):
            values=curves[k];pts=' '.join(f'{a:.3f},{b:.3f}' for a,b in (xy(t,v) for t,v in enumerate(values)))
            out.append(f'<polyline id="curve-{k}" data-values="{html.escape(json.dumps(values))}" points="{pts}" fill="none" stroke="{c}" stroke-width="3"'+(' stroke-dasharray="6 5"' if k.endswith('current') else '')+'/>')
        for t in range(0,n+1,4):text(89+930*t/n,y0+260,t,14)
        text(970,y0+285,'round',14)
        text(52,y0+305,'Final running boundary bracket:',16)
        cell(key+'-lower',330,y0+305,x['final_boundary_bracket'][0]);text(530,y0+305,'to',16)
        cell(key+'-upper',575,y0+305,x['final_boundary_bracket'][1])
    panel('constant_positive','1 Repeated positive differences','24 differences equal 1/2. The reported lower endpoint understates the exact boundary by at most 1/32768.',132)
    panel('reversal','2 A later reversal cannot erase earlier exclusions','Eight +1 then twelve -1. Current-prefix inversion weakens; the running intersection retains its lower bound.',488)
    out.append('<line x1="52" y1="842" x2="80" y2="842" stroke="#127e71" stroke-width="3"/>');text(90,848,'running-intersection lower bound',17)
    out.append('<line x1="585" y1="842" x2="613" y2="842" stroke="#c27a31" stroke-width="3" stroke-dasharray="6 5"/>');text(623,848,'current-prefix lower bound',17)
    text(42,897,'3 Exact finite-law coverage control',21,'font-weight="700"')
    text(42,927,'D is +1 with probability 3/4, otherwise -1: conditional mean 1/2 at every node, eight rounds.',16,'class="muted"')
    a=r['finite_coverage_audit']
    for x,s in ((52,'Leaf paths'),(290,'P(ever excludes 1/2)'),(600,'P(ever wealth >= 4 at 1/2)')):text(x,970,s,16,'font-weight="700"')
    cell('leaves',52,1003,a['leaf_count']);cell('exclusion',290,1003,a['exclusion_probability']);cell('crossing',600,1003,a['crossing_probability'])
    text(42,1048,'Both probabilities are 2187/16384 <= 1/4. All conditional wealth slacks are zero.',17)
    text(42,1082,'Closed outer intervals include every nonrejected mean. Rational brackets are not exact algebraic roots.',17)
    text(42,1125,'One fixed mu must upper-bound every conditional mean. Not a drifting mean or a causal effect estimate.',15,'class="muted"')
    text(42,1153,'Developed sequences and a supplied finite law. No optimality, model-selection or two-sided coverage claim.',15,'class="muted"')
    encoded=base64.b64encode(zlib.compress(json.dumps(r,sort_keys=True,separators=(',',':')).encode())).decode()
    out.append('<metadata id="report-zlib-base64">'+encoded+'</metadata></svg>')
    return '\n'.join(out)+'\n'


if __name__=='__main__':
    p=Path(__file__).resolve().parents[1]/'assets/confidence-inversion.svg';s=render(confidence_demo())
    if sys.argv[1:]==['--check']:
        if p.read_text()!=s:raise SystemExit('SVG differs')
    elif not sys.argv[1:]:p.write_text(s)
    else:raise SystemExit('usage: render_confidence.py [--check]')
