cp srg/__init__.py srg/__init__.pyx
cp srg/srg.py srg/srg.pyx
cp srg/utils.py srg/utils.pyx
cp srg/bounds.py srg/bounds.pyx
cp srg/fork.py srg/fork.pyx
cp srg/gauss_elim.py srg/gauss_elim.pyx
cp srg/partition.py srg/partition.pyx
cp srg/solver.py srg/solver.pyx
cp srg/unique.py srg/unique.pyx

python3 setup.py build_ext --inplace

