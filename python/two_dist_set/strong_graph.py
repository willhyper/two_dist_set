__author__ = 'chaoweichen'
import numpy as np
from . import representation
from . import weak_graph

def generate(seed, v,k,l,u):
    I = np.identity(v, dtype=np.int)
    J = np.ones((v, v), dtype=np.int)

    for weak in weak_graph.generate(seed):
        mat = representation.from_vectors(weak).to_matrix()
        if np.array_equal(mat@mat , (l-u)*mat + (k-u)*I + u*J):
            yield mat # strong
