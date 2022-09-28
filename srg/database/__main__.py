from srg.database import list_problems, get_solutions, draw
from srg import util
import sys
from pprint import pprint

try:
    cmd = sys.argv[1]
except IndexError:
    cmd = 'list'

try:
    v,k,l,u = list(map(int, sys.argv[2:6]))
except ValueError:
    v,k,l,u = [None]*4
    print('provide v,k,l,u arguments')

if v is None:
    pprint(list_problems())
else:
    util.assert_arg(v,k,l,u)
    if cmd == 'list':
        pprint(get_solutions(v,k,l,u))
    elif cmd == 'draw':
        draw(v,k,l,u)
    else:
        sys.exit(f'command {cmd} is not recognized. support list or draw')


