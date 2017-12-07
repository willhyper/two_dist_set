from distutils.core import setup
from Cython.Build import cythonize

setup(
    name = "Compute Adjacency Matrix for Two Distance Set",
    ext_modules = cythonize("two_dist_set/*.pyx"),
)
