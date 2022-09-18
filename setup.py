from distutils.core import setup

# https://luminousmen.com/post/resolve-cython-and-numpy-dependencies
try:
    from Cython.Build import cythonize
except ImportError:
    # create closure for deferred import
    def cythonize (*args, ** kwargs ):
        from Cython.Build import cythonize
        return cythonize(*args, ** kwargs)


setup(name='two_dist_set',
      version='1.0',
      description='Compute Adjacency Matrix for Two Distance Set, ie. Strongly regular graph',
      url='https://github.com/willhyper/two_dist_set',
      author='Chao-Wei Chen',
      author_email='willhyper@gmail.com',
      license='MIT',
      packages=['two_dist_set'],
      setup_requires=[
        'setuptools>=18.0',# so properly handles Cython extensions.
        'cython',
        ],
      install_requires=[
          'numpy',
          'pytest',
          'networkx',
          'matplotlib',
      ],
      ext_modules = cythonize("two_dist_set/*.pyx"))