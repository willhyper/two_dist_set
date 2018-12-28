'''
strongly regular graph generator
http://www.win.tue.nl/~aeb/graphs/srg/srgtab.html

65 32 15 16

'''

from . import util, strong_graph, database, cache
from pprint import pprint
import multiprocessing
from functools import reduce
import argparse


@util.timeit
def solve(cache_handler):
    p = multiprocessing.Pool(multiprocessing.cpu_count())

    @util.timeit
    def map_reduce(s_list_in) -> list:
        s_list_of_list = p.map(strong_graph.advance, s_list_in)
        return reduce(list.__iadd__, s_list_of_list)

    s_list = cache_handler.load()
    assert len(s_list) > 0
    iterations = s_list[0].len_pivot_vec

    for i in range(iterations):
        s_list = map_reduce(s_list)
        cache_handler.save(s_list)

    return s_list


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Compute and draw strongly regular graphes (SRG).')
    parser.add_argument('-p', metavar=('v', 'k', 'l', 'u'), type=int, nargs=4,
                        help='4 integers representing v, k, l, u, defining a SRG')
    parser.add_argument('-l', '--list', action='store_true', help='list SRG in database')
    args = parser.parse_args()

    if args.list:
        plist = [s for s in dir(database) if s.startswith('problem')]
        pprint(plist)
    else:

        v, k, l, u = args.p
        util.assert_arg(v, k, l, u)

        temp_file = f'pickle_{v}_{k}_{l}_{u}'
        cache_handler = cache.CacheHandler(temp_file)
        if not cache_handler.exists():
            seed = util.generate_seed(v, k, l, u)
            s_iter = [seed]
            cache_handler.save(s_iter)

        srg_solved = solve(cache_handler)

        srg_solved.sort()
        matricies = [s.to_matrix() for s in srg_solved]

        pprint(matricies)
