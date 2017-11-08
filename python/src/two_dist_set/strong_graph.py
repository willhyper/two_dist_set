__author__ = 'chaoweichen'
import numpy as np
from . import representation
from . import weak_graph
from . import globalz

def generate(seed):
    v, k, l, u = globalz.v, globalz.k, globalz.l, globalz.u
    I = np.identity(v, dtype=np.int)
    J = np.ones((v, v), dtype=np.int)
    const = (k-u)*I + u*J

    for weak in weak_graph.generate(seed):
        mat = representation.from_scalars(weak).to_matrix()

        matSQ = mat@mat

        if np.array_equal(matSQ - (l-u)*mat , const):
            yield mat # strong
