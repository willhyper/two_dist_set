import pickle
import os
from .srg import SRG


class CacheHandler:

    def __init__(self, file):
        self.file = file

    def save(self, cache):
        obj = pickle.dumps(cache)
        with open(self.file, 'wb') as f:
            f.write(obj)

        # for logging
        if len(cache) > 0:
            s : SRG = cache[0]
            print(f'saving {len(cache)} states in {s.len_pivot_vec}')
        else:
            print(f'saving process...empty')

    def load(self):
        with open(self.file, 'rb') as f:
            cache = pickle.load(f)

        # for logging
        if len(cache) > 0:
            s : SRG = cache[0]
            print(f'loading {len(cache)} states in {s.len_pivot_vec}')
        else:
            print(f'loading process...empty')

        return cache

    def exists(self):
        return os.path.exists(self.file)

