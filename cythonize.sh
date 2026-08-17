cp src/srg/__init__.py src/srg/__init__.pyx
cp src/srg/model.py src/srg/model.pyx
cp src/srg/utils.py src/srg/utils.pyx
cp src/srg/bounds.py src/srg/bounds.pyx
cp src/srg/fork.py src/srg/fork.pyx
cp src/srg/gauss_elim.py src/srg/gauss_elim.pyx
cp src/srg/partition.py src/srg/partition.pyx
cp src/srg/solver.py src/srg/solver.pyx
cp src/srg/unique.py src/srg/unique.pyx

python3 setup.py build_ext --inplace
