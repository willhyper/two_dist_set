import pickle
import os


class Handler:

    def __init__(self, v,k,l,u):
        self._file = f'pickle_{v}_{k}_{l}_{u}'

    def save(self, cache):
        obj = pickle.dumps(cache)
        with open(self._file, 'wb') as f:
            f.write(obj)

    def load(self):
        with open(self._file, 'rb') as f:
            cache = pickle.load(f)

        return cache

    def exists(self):
        return os.path.exists(self._file)

