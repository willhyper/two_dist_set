#!python
#cython: language_level=3

__author__ = 'chaoweichen'
from two_dist_set import simplifier
from two_dist_set import util
from two_dist_set.srg import SRG
import numpy as np
from multiprocessing import Pool, cpu_count
from functools import reduce
from typing import Iterator, Tuple

cpu_num = cpu_count()

def _advance_from_partition(s: SRG) -> SRG:
    A, b = s.question()
    R, C = A.shape

    if C == 0:
        # yield s
        return

    q1 = simplifier.Question(A, b)

    q2, unknown_columns = q1.reduce_zeros_from_b()

    q2R, q2C = q2.A.shape

    if q2C == 0:
        pivot_vector = np.zeros(C, dtype=int)
        yield s + pivot_vector
        return

    q3, enc_bound = q2.reduce_duplicate_columns()

    enc_smaller_bound = []
    for column, bound in enumerate(enc_bound):
        q3a = q3.A[:, column]
        b_of_interest = q3.b[q3a==1]
        smaller_bound = min(bound, b_of_interest.min()) if b_of_interest.size > 0 else bound
        enc_smaller_bound.append(smaller_bound)
    enc_smaller_bound = tuple(enc_smaller_bound)

    remain = s.k - s.used_k_of_current_row
    candidates : Iterator[Tuple] = util.partition(remain, enc_smaller_bound)

    good_candidates = filter(lambda c : np.array_equal(q3.A.dot(c), q3.b), candidates)

    binarized = map(lambda c : s + simplifier.binarize(C, unknown_columns, enc_bound, c), good_candidates)

    yield from binarized


def advance(s: SRG, approach=_advance_from_partition) -> list:
    # yield from approach(s)
    return list(approach(s)) # to be serializable for use multipleprocess

def advance_until_end(s: SRG) -> list:
    '''
    invoked by multiprocessing. Thus, within here. logic shall be single-threaded
    '''
    lst_done_final = []
    lst = advance(s)
    while lst:
        lst_undone, lst_done = partition_by_done(lst)
        lst_done_final += lst_done
        lst = reduce(lambda x,y:x+y, map(advance, lst_undone), [])
    return lst_done_final

def partition_by_done(lst : list):
    lst_undone, lst_done = [], []
    q : SRG
    for q in lst:
        if q.open:
            lst_undone.append(q)
        else:
            lst_done.append(q)
    return lst_undone, lst_done
    
def solve(s: SRG) -> SRG:
    lst : list = advance(s)
    
    # single threaded
    for i in range(2):
        lst_undone, lst_done = partition_by_done(lst)
        yield from lst_done
        lst = reduce(lambda x,y:x+y, map(advance, lst_undone), [])

        print(f'after iteration {i}, {len(lst)} questions derived')
        if not lst: break

    # multi threaded
    while lst:
        i += 1
        #
        lst_undone, lst_done = partition_by_done(lst)
        yield from lst_done
        with Pool(cpu_num) as p:
            lst = reduce(lambda x,y:x+y, p.map(advance_until_end, lst_undone), [])

        print(f'after iteration {i}, {len(lst)} questions derived')
