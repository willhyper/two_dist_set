from srg.database import list_problems, get_solutions, draw
import sys
from pprint import pprint

try:
    cmd = sys.argv[1]
except IndexError:
    cmd = 'list'

if cmd == 'status':
    from srg.database import status
    sys.exit(print(status.report(sys.argv[2] if len(sys.argv) > 2 else '.')))

try:
    v,k,l,u = list(map(int, sys.argv[2:6]))
except ValueError:
    v,k,l,u = [None]*4
    print('provide v,k,l,u arguments')

if v is None:
    pprint(list_problems())
else:
    if cmd == 'list':
        pprint(get_solutions(v,k,l,u))
    elif cmd == 'draw':
        draw(v,k,l,u)
    elif cmd == 'build':
        from srg.database import build
        extra = [a for a in sys.argv[6:] if not a.startswith('--')]
        limit = [a for a in sys.argv[6:] if a.startswith('--time-limit=')]
        print(build.build(v, k, l, u, *(int(e) for e in extra),
                          time_limit=float(limit[0].split('=')[1]) if limit else None))
    elif cmd == 'construct':
        from srg.database import build
        print(build.construct(v, k, l, u) or 'no known construction for these parameters')
    elif cmd == 'complement':
        from srg.database import build
        print(build.derive_complement(v, k, l, u))
    else:
        sys.exit(f'command {cmd} is not recognized. support list, draw, build, construct, complement or status')


