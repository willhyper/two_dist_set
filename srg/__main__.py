from .solver import _seed, solve
from .srg import Question, SRG, NoSolution
from . import pprint, persist
import sys
import multiprocessing
import itertools


def dfs_mat(mat):
    return list(dfs_mat_gen(mat))


def dfs_mat_gen(mat):
    srg = SRG(mat)

    stack = list()
    stack.append(srg)
    while stack:
        print(f'pending list = {len(stack)}')
        srg: SRG = stack.pop()
        if srg.solved():
            yield srg.current_matrix
        else:

            for ans in wfs_row(srg.current_matrix):
                srg_next: SRG = srg.append_and_return_new(ans)
                stack.append(srg_next)

                # print(f'candidate: {ans}')


def wfs_row(mat):
    try:
        Q: Question = Question.from_matrix(mat, v, k, l, u)
    except NoSolution as e:
        # pprint.red(e)
        pass
    else:
        # pprint.yellow(mat)
        return list(solve(Q))


def wfs_mat(mat):
    srg: SRG = SRG(mat)
    return [srg._append_and_return_new(row) for row in wfs_row(mat)]


def assert_srg(v: int, k: int, l: int, u: int):
    assert (v - k - 1) * u == k * (k - l - 1), f'{(v,k,l,u)} is not a strongly regular graph problem.'


if __name__ == '__main__':
    pprint.clear()

    v, k, l, u = map(int, sys.argv[1:])
    print(v, k, l, u)

    assert_srg(v, k, l, u)

    mat = _seed(v, k, l, u)


    def multithreaded(mat):
        map_wfs_mat = lambda mat_list: list(itertools.chain(*map(wfs_mat, mat_list)))
        next_mat_candidates = [mat]
        next_mat_candidates = map_wfs_mat(next_mat_candidates)
        print(len(next_mat_candidates))
        next_mat_candidates = map_wfs_mat(next_mat_candidates)
        print(len(next_mat_candidates))

        p = multiprocessing.Pool(multiprocessing.cpu_count())
        anslist_of_list = p.map(dfs_mat, next_mat_candidates)
        return list(itertools.chain(*anslist_of_list))


    def singlethreaded(mat):
        return dfs_mat(mat)

    anslist = multithreaded(mat)
    # anslist = singlethreaded(mat)

    # persist
    ph = persist.Handler(v,k,l,u)
    ph.save(anslist)

    #
    pprint.green('*********** answers *************')
    for ans in anslist:
        pprint.green(ans)
