"""Deterministic SVG with exact report metadata. Decimal pixels only for drawing."""
import base64
from fractions import Fraction as F
import html
import json
from pathlib import Path
import sys
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from betlab import demo


def render(report):
    colors={'mixture':'#127e71','predictable':'#485fa8','invalid_restart':'#b0473f'}
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="1030" viewBox="0 0 1120 1030">',
           '<rect width="1120" height="1030" fill="#f4f1ed"/>',
           '<rect x="16" y="16" width="1088" height="998" rx="18" fill="#fff"/>',
           '<style>text{font-family:Arial,sans-serif;fill:#292929}.muted{fill:#666}.small{font-size:14px}</style>']
    def text(x,y,s,size=18,extra=''):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{html.escape(s)}</text>')
    text(42,58,'BetLab / evidence survives optional stopping, not free restarts',26,'font-weight="700"')
    text(42,86,'Exact rational betting for bounded paired model-score differences. No model benchmark.',16,'class="muted"')
    text(42,130,'1 A crossing can remain valid even when current wealth later falls',21,'font-weight="700"')
    text(42,157,'Eight +1 differences, then twelve -1. Vertical coordinate: log2(1 + wealth).',15,'class="muted"')
    # Plot complete trace, zeros included; log is display only, not test arithmetic.
    import math
    def xy(t,v):return 95+46*t, 430-30*math.log2(1+float(F(v)))
    for v in (0,1,4,16,64,256):
        _,y=xy(0,str(v));parts.append(f'<line x1="95" y1="{y:.3f}" x2="1015" y2="{y:.3f}" stroke="#e5e5e5"/>');text(50,y+5,str(v),14)
    _,y=xy(0,'4');parts.append(f'<line x1="95" y1="{y:.3f}" x2="1015" y2="{y:.3f}" stroke="#333" stroke-dasharray="6 5"/>')
    text(870,y-8,'threshold 4',14)
    for k,c in colors.items():
        values=['1']+[r[k] for r in report['cross_then_reverse']['trace']]
        pts=' '.join(f'{x:.3f},{y:.3f}' for x,y in (xy(t,v) for t,v in enumerate(values)))
        parts.append(f'<polyline id="curve-{k}" data-values="{html.escape(json.dumps(values))}" points="{pts}" fill="none" stroke="{c}" stroke-width="3"/>')
    for t in (0,4,8,12,16,20):text(90+46*t,455,str(t),14)
    text(1000,480,'time',14)
    for j,(k,c) in enumerate(colors.items()):
        parts.append(f'<line x1="{60+340*j}" y1="500" x2="{85+340*j}" y2="500" stroke="{c}" stroke-width="3"/>');text(92+340*j,505,k.replace('_',' '),16)
    text(42,550,'2 Exhaustive fair-null tree: 256 paths, eight rounds, alpha = 1/4',21,'font-weight="700"')
    text(42,579,'At every history P(+1)=P(-1)=1/2. Valid processes start at one, without refills.',15,'class="muted"')
    for j,(s,x) in enumerate((('Process',52),('P(ever >= 4)',425),('E(final wealth)',640),('E(stopped wealth)',850))):text(x,622,s,16,'font-weight="700"')
    summary=report['fair_coin_audit']['summary']
    for i,(k,c) in enumerate(colors.items()):
        y=662+43*i;text(52,y,k.replace('_',' '),17)
        for j,key in enumerate(('crossing_probability','expected_final_wealth','expected_stopped_wealth')):
            val=summary[k][key];x=(425,640,850)[j]
            text(x,y,val,18,f'id="cell-{k}-{key}" data-value="{val}"')
    text(42,810,'Restart comparator crosses with probability 201/256 > 1/4. It injects new capital at ruin.',17)
    text(42,842,'The node audit exposes negative conditional slack at reset histories. It is not an e-process.',16,'class="muted"')
    text(42,889,'3 Paired-score fixture: baseline 1/2, candidate 3/4, 32 rounds',21,'font-weight="700"')
    text(42,922,'At alpha 1/20: fixed-mixture crossing 19; past-only strategy crossing 17. Descriptive only.',16)
    text(42,962,'Validity requires E[difference_t | past] <= 0 under the null, bounded scores and a prespecified test.',15,'class="muted"')
    text(42,988,'No guarantee for marginal-mean-only nulls, post-hoc stream choice, model selection or repeated refills.',15,'class="muted"')
    encoded=base64.b64encode(zlib.compress(json.dumps(report,sort_keys=True,separators=(',',':')).encode())).decode()
    parts.append('<metadata id="report-zlib-base64">'+encoded+'</metadata></svg>')
    return '\n'.join(parts)+'\n'


if __name__=='__main__':
    target=Path(__file__).resolve().parents[1]/'assets/evidence-audit.svg'
    out=render(demo())
    if sys.argv[1:]==['--check']:
        if target.read_text()!=out:raise SystemExit('SVG differs')
    elif not sys.argv[1:]:target.write_text(out)
    else:raise SystemExit('usage: render_demo.py [--check]')
