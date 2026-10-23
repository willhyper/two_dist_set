#!python
#cython: language_level=3
"""Exact shared seen keys in packed open-addressed tables, without per-key objects.

Tables are grouped by (rows built, key length). Each slot contains one occupancy
byte and the complete canonical key. Python's hash chooses a starting slot only;
full byte comparison resolves collisions. Keys are never evicted or truncated.
"""
from multiprocessing.managers import BaseManager
from threading import Lock


class _KeyTable:
    def __init__(self, width):
        self.width = width
        self.capacity = 8
        self.count = 0
        self.data = bytearray(self.capacity * (width + 1))

    def _slot(self, key):
        stride = self.width + 1
        slot = hash(key) & (self.capacity - 1)
        while self.data[slot * stride]:
            offset = slot * stride + 1
            if self.data.startswith(key, offset, offset + self.width):
                return slot, True
            slot = (slot + 1) & (self.capacity - 1)
        return slot, False

    def _write(self, slot, key):
        offset = slot * (self.width + 1)
        self.data[offset] = 1
        self.data[offset + 1:offset + 1 + self.width] = key

    def _grow(self):
        previous = self.data
        stride = self.width + 1
        self.capacity *= 2
        self.data = bytearray(self.capacity * stride)
        for offset in range(0, len(previous), stride):
            if previous[offset]:
                key = bytes(previous[offset + 1:offset + stride])
                slot, _ = self._slot(key)
                self._write(slot, key)

    def add(self, key):
        """Return True only when the complete key was not previously stored."""
        slot, present = self._slot(key)
        if present:
            return False
        if (self.count + 1) * 3 > self.capacity * 2:
            self._grow()
            slot, _ = self._slot(key)
        self._write(slot, key)
        self.count += 1
        return True


class SharedSeen:
    """Manager-owned exact set; all claim operations are atomic across workers."""
    def __init__(self):
        self.tables = {}
        self.lock = Lock()

    def claim(self, rows, key):
        with self.lock:
            group = (rows, len(key))
            table = self.tables.get(group)
            if table is None:
                table = self.tables[group] = _KeyTable(len(key))
            return table.add(key)

    def stats(self):
        """Counts and allocated slot bytes, excluding fixed Python object headers."""
        with self.lock:
            return {
                'keys': sum(t.count for t in self.tables.values()),
                'payload_bytes': sum(t.count * t.width for t in self.tables.values()),
                'table_bytes': sum(len(t.data) for t in self.tables.values()),
                'groups': len(self.tables),
            }


class SeenManager(BaseManager):
    pass


SeenManager.register('SharedSeen', SharedSeen)
