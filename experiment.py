from collections import deque

import two_dist_set
import time
from functools import wraps

call_counter = 0

def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global call_counter

        call_counter += 1
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f'{call_counter} {func.__name__} elapsed sec {elapsed}')

        return result

    return wrapper

@timeit
def advance(s):
    return list(two_dist_set.strong_graph._advance_from_partition(s))


def map_reduce(s_list: list):
    s_list_list = map(advance, s_list)
    return reduce(list.__iadd__, s_list_list)


if __name__ == '__main__':
    from functools import reduce
    from two_dist_set.database import *

    v, k, l, u, matrices = problem_9_4_1_2

    s = two_dist_set.util.generate_seed(v, k, l, u)

    s_list = [s]

    iterations = v - s.state - 1
    for i in range(iterations):
        s_list = map_reduce(s_list)
        print(s_list)