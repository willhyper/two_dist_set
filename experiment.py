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


if __name__ == '__main__':
    from two_dist_set.database import *

    v, k, l, u, matrices = problem_25_8_3_2

    s = two_dist_set.util.generate_seed(v, k, l, u)

    q = deque()
    q.append(s)

    while q:

        s = q.pop()
        pt = advance(s)

        for ss in pt:
            q.append(ss)
