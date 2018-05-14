import time
from functools import wraps
import pickle
import os
from two_dist_set.conference import conference
import numpy as np

from two_dist_set.srg import SRG
from collections import defaultdict



def assert_arg(v: int, k: int, l: int, u: int):
    assert (v - k - 1) * u == k * (k - l - 1), f'{(v,k,l,u)} is not a strongly regular graph problem.'


def eig(v: int, k: int, l: int, u: int):
    conf = conference(v, k, l, u)  # if conference graph, conf == 0, so D becomes non-integer

    D = np.sqrt((l - u) ** 2 + 4 * (k - u))
    D = int(D) if conf != 0 else D

    eig = k, ((l - u) + D) / 2, ((l - u) - D) / 2
    eig = tuple(int(x) if conf != 0 else x for x in eig)  # if not conference graph, eigvalues are integer
    mul = 1, int(((v - 1) - conf / D) / 2), int(((v - 1) + conf / D) / 2)  # multiplicity is always integer

    return tuple(zip(eig, mul))


def determinant(v: int, k: int, l: int, u: int):
    prod = 1
    for e, m in eig(v, k, l, u):
        prod *= e ** m

    return int(round(prod))


def generate_seed(v: int, k: int, l: int, u: int):
    first_row = np.zeros(v - 1, dtype=np.int)
    first_row[:k] = 1

    s = SRG(v, k, l, u)
    s += first_row

    second_row = np.zeros(v - 2, dtype=np.int)

    remain_ones_number = k - l - 1
    second_row[:l] = 1
    second_row[k - 1:k + remain_ones_number - 1] = 1

    s += second_row
    return s


def gauss_eliminate(A, b):
    '''
    a non-ideal (buggy) version of Gauss elimination
    :param A: m by n matrix
    :param b: m by 1 vector
    :return: A_reduced, b_reduced
    '''
    R, C = A.shape
    b = np.expand_dims(b, axis=1)
    Ab = np.hstack((A, b))

    row_to_nonzero_columns = defaultdict(list)
    for c in range(C):
        nonzero_rows = Ab[:, c].nonzero()[0]
        # [0] to select the 1st element in the tuple because Ab[:, c] is a 1D vector

        if len(nonzero_rows) < 2:
            continue

        # use nonzero_rows to construct
        row_to_nonzero_columns.clear()
        for rr, cc in zip(*Ab[nonzero_rows, :].nonzero()):
            row_to_nonzero_columns[rr].append(cc)

        lenmap = map(len, row_to_nonzero_columns.values())
        argmin = np.argmin(list(lenmap))
        row_0 = nonzero_rows[argmin]
        row_rest = np.setdiff1d(nonzero_rows, row_0)

        e = Ab[row_0, c]
        if e != 1:
            Ab[row_rest, :] *= e

        v = Ab[row_0, :].reshape((1, -1))
        ratio = Ab[row_rest, c].reshape((-1, 1))
        Ab[row_rest, :] -= ratio @ v

    return Ab[:, :-1], Ab[:, -1]



def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):

        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f'{func.__name__} elapsed sec {elapsed}')

        return result

    return wrapper

class CacheHandler:

    def __init__(self, file):
        self.file = file

    def save(self, cache):
        obj = pickle.dumps(cache)
        with open(self.file, 'wb') as f:
            f.write(obj)

        # for logging
        if len(cache) > 0:
            s : SRG = cache[0]
            print(f'saving {len(cache)} states in {s.len_pivot_vec}')
        else:
            print(f'saving process...empty')

    def load(self):
        with open(self.file, 'rb') as f:
            cache = pickle.load(f)

        # for logging
        if len(cache) > 0:
            s : SRG = cache[0]
            print(f'loading {len(cache)} states in {s.len_pivot_vec}')
        else:
            print(f'loading process...empty')

        return cache

    def exists(self):
        return os.path.exists(self.file)

