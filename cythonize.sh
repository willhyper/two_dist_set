cp srg/__init__.py srg/__init__.pyx
cp srg/strong_graph.py srg/strong_graph.pyx
cp srg/weak_graph.py srg/weak_graph.pyx
cp srg/sort.py srg/sort.pyx
cp srg/srg.py srg/srg.pyx
cp srg/simplifier.py srg/simplifier.pyx
cp srg/util.py srg/util.pyx

python3 setup.py build_ext --inplace

