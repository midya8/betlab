"""Prespecified start allocation figure; exact evidence, floating display coordinates."""
import base64
from fractions import Fraction as F
import html
import json
import math
from pathlib import Path
import sys
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from betlab import starts_demo


def render(r):
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="1080" viewBox="0 0 1120 1080">',
         '<rect width="1120" height="1080" fill="#f4f1ed"/><rect x="16" y="16" width="1088" height="1048" rx="18" fill="white"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#292929}.muted{fill:#666}</style>']
    def text(x,y,s,size=17,extra=''):
        out.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{html.escape(str(s))}</text>')
    def cell(id,x,y,s):text(x,y,s,18,f'id="cell-{id}" data-value="{s}"')
    text(42,58,'BetLab / planned starts share one unit, not unlimited refills',26,'font-weight="700"')
    text(42,87,'A fixed finite mixture keeps future capital reserved and ruined components at zero.',17,'class="muted"')
    text(42,130,'1 Late evidence after an early loss',21,'font-weight="700"')
    text(42,158,'Eight -1 differences, eight +1, then eight -1. Bet one; starts 1, 9, 17 each receive 1/3.',16,'class="muted"')
    def xy(t,v):return 95+38*t, 425-31*math.log2(1+float(F(v)))
    for v in (0,1,4,16,64):
        _,y=xy(0,v);out.append(f'<line x1="95" y1="{y:.3f}" x2="1007" y2="{y:.3f}" stroke="#e5e5e5"/>');text(55,y+5,v,14)
    _,y=xy(0,4);out.append(f'<line x1="95" y1="{y:.3f}" x2="1007" y2="{y:.3f}" stroke="#333" stroke-dasharray="6 5"/>');text(870,y-8,'threshold 4',14)
    for start in (9,17):
        x,_=xy(start,0);out.append(f'<line x1="{x}" y1="205" x2="{x}" y2="425" stroke="#bbb" stroke-dasharray="3 4"/>');text(x-28,194,'start '+str(start),14)
    curves={'scheduled':['1']+[a['wealth'] for a in r['delayed_signal']['trace']],
            'from_start':['1']+[a['mixture'] for a in r['from_start_control']['trace']]}
    for k,c in (('scheduled','#127e71'),('from_start','#485fa8')):
        pts=' '.join(f'{x:.3f},{y:.3f}' for x,y in (xy(t,v) for t,v in enumerate(curves[k])))
        out.append(f'<polyline id="curve-{k}" data-values="{html.escape(json.dumps(curves[k]))}" points="{pts}" fill="none" stroke="{c}" stroke-width="3"/>')
    for t in (0,4,8,12,16,20,24):text(90+38*t,452,t,14)
    text(980,480,'time',14)
    out.append('<line x1="60" y1="500" x2="88" y2="500" stroke="#127e71" stroke-width="3"/>');text(98,506,'allocated start mixture',17)
    out.append('<line x1="465" y1="500" x2="493" y2="500" stroke="#485fa8" stroke-width="3"/>');text(503,506,'one process from round 1',17)
    text(52,552,'First crossing',16);cell('delayed-cross',52,580,r['delayed_signal']['decision']['first_crossing'])
    text(385,552,'Final wealth',16);cell('delayed-final',385,580,r['delayed_signal']['decision']['final_wealth'])
    text(710,552,'Unstarted budget at round 16',16);cell('delayed-reserve',710,580,r['delayed_signal']['trace'][15]['unstarted_budget'])
    text(42,628,'2 Exhaustive null-law audit, alpha = 1/4',21,'font-weight="700"')
    text(42,656,'Starts 1, 3, 5, 9 each receive 1/4; the round-9 budget stays reserved in both trees.',16,'class="muted"')
    for x,s in ((52,'Null tree'),(415,'P(ever >= 4)'),(645,'E(final wealth)'),(855,'E(stopped wealth)')):text(x,700,s,16,'font-weight="700"')
    for i,(k,label) in enumerate((('fair_null','Fair signs, 8 rounds'),('negative_drift_null','P(+1)=1/3, 6 rounds'))):
        y=743+48*i;text(52,y,label,17)
        for j,field in enumerate(('crossing_probability','expected_final_wealth','expected_stopped_wealth')):cell(k+'-'+field,(415,645,855)[j],y,r[k]['summary'][field])
    text(42,850,'The invalid free-refill control still crosses with probability 201/256 in the fair tree.',17)
    text(42,882,'The planned mixture crosses with probability 5/32 <= 1/4; no unbudgeted capital is added.',17)
    text(42,930,'For start s: K(s,t)=1 before s, then multiply 1+b*D from s onward.',17)
    text(42,960,'Fixed nonnegative start/bet weights sum to one, including the unstarted reserve.',17)
    text(42,1000,'One prespecified conditional-mean-null test. Not a change-time estimate or a general power ranking.',15,'class="muted"')
    text(42,1028,'No adaptive/post-hoc starts, infinite-horizon restart service, ARL detector or model-selection correction.',15,'class="muted"')
    encoded=base64.b64encode(zlib.compress(json.dumps(r,sort_keys=True,separators=(',',':')).encode())).decode()
    out.append('<metadata id="report-zlib-base64">'+encoded+'</metadata></svg>')
    return '\n'.join(out)+'\n'


if __name__=='__main__':
    p=Path(__file__).resolve().parents[1]/'assets/start-allocation.svg';s=render(starts_demo())
    if sys.argv[1:]==['--check']:
        if p.read_text()!=s:raise SystemExit('SVG differs')
    elif not sys.argv[1:]:p.write_text(s)
    else:raise SystemExit('usage: render_starts.py [--check]')
