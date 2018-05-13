python -m pytest --cache-show

python -m pytest --last-failed-no-failures none # if no last failures, run no tests
python -m pytest -vs --last-failed --durations=0 tests/

# python -m pytest --cache-clear