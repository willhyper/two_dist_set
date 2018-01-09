__author__ = 'chaoweichen'

from . import weak_graph
from two_dist_set.srg import SRG
from types import coroutine


@coroutine
def filter_coroutine(s: SRG):
    if s.unknown_len_of_current_row == 0:
        return

    M_right, inner_prod_remain = s.question()

    pass_fail = None
    while True:
        vec = yield pass_fail
        pass_fail = False

        inner_prod_actual = M_right @ vec

        for actual, remain in zip(inner_prod_actual, inner_prod_remain):
            if actual != remain:
                break
        else:
            pass_fail = True


def _advance(s: SRG):
    fltr = filter_coroutine(s)
    fltr.send(None)  # prime

    for weak in weak_graph.advance(s):
        pass_fail = fltr.send(weak)
        if pass_fail:
            yield s + weak


def advance(s: SRG):
    yield from _advance(s)
