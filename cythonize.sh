#!/bin/sh
# Opt-in Cython build: compile every pure-Python module of the package in place.
# __main__.py stays a plain script so `python -m srg` keeps working; database/ is data.
for f in src/srg/*.py; do
    case "$f" in
        */__main__.py) ;;
        *) cp "$f" "${f%.py}.pyx" ;;
    esac
done

python3 setup.py build_ext --inplace
