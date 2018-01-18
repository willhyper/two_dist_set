from collections import deque

import two_dist_set


if __name__ == '__main__':
    from two_dist_set.problem_database import *

    v, k, l, u, matrices = problem_25_8_3_2

    s = two_dist_set.util.generate_seed(v, k, l, u)

    q = deque()
    q.append(s)

    while q:

        s = q.pop()
        pt = list(two_dist_set.strong_graph._advance_from_partition(s))

        for ss in pt:
            q.append(ss)