import json
import sys
from pathlib import Path
from . import replay, paired, audit_tree, demo


def pairs(items):
    result = {}
    for k, v in items:
        if k in result:
            raise ValueError('duplicate JSON key')
        result[k] = v
    return result


def main():
    try:
        args = sys.argv[1:]
        if args == ['demo']:
            result = demo()
        elif len(args) == 2 and args[0] in ('replay', 'paired', 'tree'):
            raw = Path(args[1]).read_bytes()
            if len(raw) > 200000:
                raise ValueError('input exceeds 200000 bytes')
            x = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
            if not isinstance(x, dict) or type(x.get('schema_version')) is not int or x['schema_version'] != 1:
                raise ValueError('schema_version must be integer one')
            required = {'replay': {'differences'}, 'paired': {'baseline', 'candidate'}, 'tree': {'tree'}}[args[0]]
            allowed = required | {'schema_version', 'bets', 'weights', 'alpha'}
            if not required <= set(x) or not set(x) <= allowed:
                raise ValueError('input schema mismatch')
            kw = {k: x[k] for k in ('bets', 'weights', 'alpha') if k in x}
            if args[0] == 'replay':
                result = replay(x['differences'], **kw)
            elif args[0] == 'paired':
                result = paired(x['baseline'], x['candidate'], **kw)
            else:
                result = audit_tree(x['tree'], **kw)
        else:
            raise ValueError('usage: python -m betlab demo | replay FILE | paired FILE | tree FILE')
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, RecursionError) as exc:
        print('error: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
