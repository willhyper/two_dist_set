# what this is?
complete enumeration to construct strongly regular graph

# intro
a [strongly regular graph](https://en.wikipedia.org/wiki/Strongly_regular_graph) is specified by 4 integer parameters (v,k,l,u), such as (4,2,0,2), (13,6,2,3),...
# setup
```
git clone https://github.com/willhyper/two_dist_set.git
cd two_dist_set
mkdir .venv
pipenv install Pipfile -d
pipenv shell
```
# example usage:
1. generate adjacency matrix
```python
python -m two_dist_set -p 13 6 2 3

...
array([[0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
       [1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0],
       [1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0],
       [1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 1],
       [1, 0, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 1],
       [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0],
       [1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 1],
       [0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1],
       [0, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1],
       [0, 1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0],
       [0, 0, 1, 1, 0, 1, 0, 1, 0, 0, 0, 1, 1],
       [0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1, 0, 0],
       [0, 0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0]])
...       
```
2. run tests
```
./run_all_tests.sh
./run_last_failed_test.sh

========================================= test session starts ==========================================
platform darwin -- Python 3.6.5, pytest-3.5.1, py-1.5.3, pluggy-0.6.0 -- /.venv/bin/python
cachedir: .pytest_cache
rootdir: /Users/chaoweichen/repo/two_dist_set, inifile:
collected 134 items                                                                                    
run-last-failure: run all (no recorded failures)

tests/test_database.py::test_matrix_property[4-2-0-2-database0] PASSED
tests/test_database.py::test_matrix_property[5-2-0-1-database1] PASSED
tests/test_database.py::test_matrix_property[6-3-0-3-database2] PASSED
...
```

3. list database (of course this is an incomplete set)
```
python -m two_dist_set -l
['problem_10_3_0_1',
 'problem_10_6_3_4',
 'problem_12_6_0_6',
 'problem_13_6_2_3',
 'problem_15_6_1_3',
 'problem_15_8_4_4',
 'problem_16_10_6_6',
 'problem_16_5_0_2',
 'problem_16_6_2_2',
 'problem_16_9_4_6',
...
```
4. plot graph (if there is answer in database)
```
frameworkpython -m two_dist_set -p 10 6 3 4 --draw
```
it generates srg_10_6_3_4.png in current directory

5. Cythonize & uncythonize
```
./cythonize.sh
python -m two_dist_set -p 13 6 2 3
./uncythonize.sh

```

# troubleshoot
1. [matplotlib requires a framework python](https://matplotlib.org/faq/osx_framework.html)
```
RuntimeError: Python is not installed as a framework. The Mac OS X backend will not be able to function correctly if Python is not installed as a framework. See the Python documentation for more information on installing Python as a framework on Mac OS X. Please either reinstall Python as a framework, or try one of the other backends. If you are using (Ana)Conda please install python.app and replace the use of 'python' with 'pythonw'. See 'Working with Matplotlib on OSX' in the Matplotlib FAQ for more information.
```

# todo:
enforce AJ = JA 
after fork_enum clean up the original question?
namba
zero_in_b remove 0 rows

# hypotheses:
after midway, no more fork_enum is needed
