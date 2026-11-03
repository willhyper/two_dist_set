"""Optional Rust C ABI binding. Buffers stay Python-owned; CDLL releases the GIL."""
import ctypes
import os
from pathlib import Path
import sys

import numpy as np


def load():
    backend = os.environ.get('SRG_CANON_BACKEND', 'auto')
    if backend not in ('auto', 'python', 'rust'):
        raise ValueError('SRG_CANON_BACKEND must be auto, python, or rust')
    if backend == 'python':
        return None
    suffix = '.dll' if sys.platform == 'win32' else '.dylib' if sys.platform == 'darwin' else '.so'
    path = Path(__file__).with_name('_canon_rust' + suffix)
    if not path.exists():
        if backend == 'rust':
            raise ImportError('Rust canonicalizer is not built; run python build_rust.py')
        return None
    library = ctypes.CDLL(str(path))
    library.srg_canon_abi_version.argtypes = []
    library.srg_canon_abi_version.restype = ctypes.c_uint32
    if library.srg_canon_abi_version() != 1:
        raise ImportError('Rust canonicalizer ABI mismatch; rebuild with python build_rust.py')
    function = library.srg_canonical_key
    function.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_size_t, ctypes.c_size_t,
                         ctypes.c_int64, ctypes.c_void_p, ctypes.c_size_t,
                         ctypes.POINTER(ctypes.c_size_t)]
    function.restype = ctypes.c_int

    def canonical(matrix, leaf_budget):
        matrix = np.asarray(matrix)
        if matrix.ndim != 2 or matrix.shape[0] > matrix.shape[1]:
            raise ValueError('expected an R x v partial matrix with R <= v')
        # Avoid silently wrapping wide integers/floats when converting to bytes.
        if matrix.dtype not in (np.dtype('int8'), np.dtype('uint8'), np.dtype('bool')):
            if not np.all((matrix == 0) | (matrix == 1)):
                raise ValueError('canonicalization requires binary entries')
        # Own the input while the GIL is released, including for contiguous
        # arrays: callers may otherwise mutate their NumPy array concurrently.
        data = np.array(matrix, dtype=np.uint8, order='C', copy=True)
        rows, columns = data.shape
        budget = int(leaf_budget)
        if not -(2 ** 63) <= budget < 2 ** 63:
            raise OverflowError('leaf budget must fit a signed 64-bit integer')
        bits = columns - rows + rows * (rows - 1) // 2 + rows * (columns - rows)
        capacity = max(1, (bits + 7) // 8)
        output = ctypes.create_string_buffer(capacity)
        length = ctypes.c_size_t()
        code = function(data.ctypes.data, data.size, rows, columns, budget,
                        output, capacity, ctypes.byref(length))
        if code == 1:
            return None
        if code == -1:
            raise ValueError('invalid partial matrix (binary, symmetric built block required)')
        if code != 0:
            raise RuntimeError('Rust canonicalization failed with status ' + str(code))
        if length.value > capacity:
            raise RuntimeError('Rust canonicalization returned an invalid length')
        return output.raw[:length.value]

    # Keep the loaded library alive with its function wrapper.
    canonical.library = library
    return canonical
