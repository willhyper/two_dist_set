cp two_dist_set/__init__.py two_dist_set/__init__.pyx
cp two_dist_set/strong_graph.py two_dist_set/strong_graph.pyx
cp two_dist_set/weak_graph.py two_dist_set/weak_graph.pyx
cp two_dist_set/sort.py two_dist_set/sort.pyx
cp two_dist_set/srg.py two_dist_set/srg.pyx
cp two_dist_set/simplifier.py two_dist_set/simplifier.pyx
cp two_dist_set/util.py two_dist_set/util.pyx

python setup.py build_ext --inplace

