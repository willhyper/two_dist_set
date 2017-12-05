__author__ = 'chaoweichen'
import numpy as np
from . import representation
from . import weak_graph


def check_problem(v,k,l,u):
    return (v-k-1) * u == k*(k-l-1)


def generate_seed(v,k,l,u):
    return 2**(v-1) - 2**(v-k-1),  # tuple of numbers


def generate(seed,v, k, l, u):
    I = np.identity(v, dtype=np.int)
    J = np.ones((v, v), dtype=np.int)
    const = (k-u)*I + u*J

    for weak in weak_graph.generate(seed, v, k, l, u):
        mat = representation.from_scalars(weak, v, k, l, u).to_matrix()

        matSQ = mat@mat

        if np.array_equal(matSQ - (l-u)*mat , const):
            yield mat # strong
