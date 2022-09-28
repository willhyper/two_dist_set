#!python
#cython: language_level=3

from .srg import SRG, Question, array, NoSolution
from typing import Iterator
from functools import reduce
from . import pprint
from . import utils
from . import solver
import sys

def partition_by_done(lst : Iterator[SRG]):
    lst_done, lst_undone = [], []
    [lst_done.append(s) if s.solved() else lst_undone.append(s) for s in lst]
    return lst_done, lst_undone

def advance(s : SRG) -> Iterator[SRG]:
    assert not s.solved()
    try:
        q = Question.from_matrix(s.current_matrix)
    except NoSolution:
        return []
    ansgen_arr : Iterator[array] = solver.solve(q)
    return list(map(s.append_and_return_new, ansgen_arr))

def main(mat):
    srg = SRG(mat)
    lst = advance(srg)
    lst_done, lst_undone = partition_by_done(lst)
    yield from [s.current_matrix for s in lst_done]    
    lst = reduce(lambda x,y: x+y, map(advance, lst_undone),[])
    while lst:        
        lst_done, lst_undone = partition_by_done(lst)
        yield from [s.current_matrix for s in lst_done]
        lst = reduce(lambda x,y: x+y, map(advance, lst_undone),[])

if __name__ == '__main__':
    pprint.clear()

    v, k, l, u = map(int, sys.argv[1:])
    print(v, k, l, u)

    utils.assert_srg(v, k, l, u)

    mat = solver._seed(v, k, l, u)
    ansgen = main(mat)

    anslist :list = [ans for ans in ansgen]

    pprint.green('*********** answers *************')
    for ans in anslist:
        pprint.green(ans)
