#!python
#cython: language_level=3
from .solver import _seed, solve
from .srg import Question, SRG, NoSolution
from . import pprint
from . import utils
import sys


def main(mat, v, k, l, u):
    srg = SRG(mat)

    stack = list()
    stack.append(srg)
    while stack:
        print(f'pending list = {len(stack)}')
        srg: SRG = stack.pop()
        if srg.solved():
            yield srg.current_matrix
        else:

            try:
                Q: Question = Question.from_matrix(srg.current_matrix, v, k, l, u)
            except NoSolution as e:
                # pprint.red(e)
                continue
            else:
                # pprint.yellow(srg.current_matrix)
                for ans in solve(Q):
                    srg_next: SRG = srg.append_and_return_new(ans)
                    stack.append(srg_next)

                    print(f'candidate: {ans}')


if __name__ == '__main__':
    pprint.clear()

    v, k, l, u = map(int, sys.argv[1:])
    print(v, k, l, u)

    utils.assert_srg(v, k, l, u)

    mat = _seed(v, k, l, u)
    ansgen = main(mat, v, k, l, u)

    anslist :list = [ans for ans in ansgen]

    pprint.green('*********** answers *************')
    for ans in anslist:
        pprint.green(ans)
