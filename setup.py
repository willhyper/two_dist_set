'''
Standalone helper for the OPT-IN Cython build (see cythonize.sh / uncythonize.sh).
NOT used by `pip install` -- all packaging metadata lives in pyproject.toml. This only
runs ext_modules through Cython when .pyx files actually exist, so it's always safe to
invoke (directly, or incidentally as part of a normal setuptools build).
'''
import glob
from setuptools import setup

pyx_files = glob.glob("src/srg/*.pyx")
ext_modules = []
if pyx_files:
    from Cython.Build import cythonize
    ext_modules = cythonize(pyx_files)

setup(ext_modules=ext_modules)
