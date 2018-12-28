import numpy as np


def enum(s: int, bounds) -> tuple:
    assert s >= 0, "sum to be placed is required >= 0"

    l = len(bounds)
    assert l >= 1, "len(dict) is required >= 1"

    bound, *others = bounds

    if l > 1:

        for v in range(min(bound, s) + 1):
            rem = s - v

            for t in enum(rem, others):
                yield (v,) + t

    else:
        if s <= bound:
            yield (s,)


def lower_upper_bound(A: np.array, b: np.array, bounds: list) -> None:
    for row, lower_upper_bound in zip(A, b):
        nonzeros = np.nonzero(row)[0]
        # print(row, lower_upper_bound, nonzeros)
        # [0 0 0 0 1] 1 [4]
        # [0 0 1 1 0] 1 [2 3]
        # [1 0 1 0 0] 0 [0 2]
        # [1 1 0 0 0] 1 [0 1]
        for loc in nonzeros:
            bounds[loc] = min(bounds[loc], lower_upper_bound)


if __name__ == '__main__':
    A = np.array([[0, 0, 0, 0, 1],
                  [0, 0, 1, 1, 0],
                  [1, 0, 1, 0, 0],
                  [1, 1, 0, 0, 0]], dtype=np.int8)
    b = np.array([1, 1, 0, 1], dtype=np.int8)

    bounds = [1, 1, 1, 1, 1]
    ans = [0, 1, 0, 1, 1]

    print('original upper bounds', bounds)
    lower_upper_bound(A, b, bounds)
    print('new lower upper bounds', bounds)

    for e in enum(3, bounds): print(e)