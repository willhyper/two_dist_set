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
        self.duplicate_hits = 0
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
            self.duplicate_hits += 1
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
        self.local_counts = {}

    def claim(self, rows, key):
        with self.lock:
            group = (rows, len(key))
            table = self.tables.get(group)
            if table is None:
                table = self.tables[group] = _KeyTable(len(key))
            return table.add(key)

    def record_local(self, counts):
        """Batch worker-local rejections and canonicalization skips once per slice."""
        with self.lock:
            for rows, (duplicates, skipped) in counts.items():
                previous = self.local_counts.setdefault(rows, [0, 0])
                previous[0] += duplicates
                previous[1] += skipped

    def stats(self):
        """Snapshot of partial-key storage and rejection counts, without key copies.

        Slot bytes include occupancy and unused capacity, excluding Python object
        headers and temporary resize buffers. Local counts arrive at slice end;
        shared counts include live claims. Neither is a count of saved expansions.
        """
        with self.lock:
            groups = []
            by_rows = {}
            for (rows, width), table in sorted(self.tables.items()):
                entry = {
                    'rows': rows, 'key_bytes': width, 'keys': table.count,
                    'payload_bytes': table.count * width,
                    'table_bytes': len(table.data),
                    'shared_duplicate_hits': table.duplicate_hits,
                }
                groups.append(entry)
                row = by_rows.setdefault(rows, {
                    'keys': 0, 'payload_bytes': 0, 'table_bytes': 0,
                    'shared_duplicate_hits': 0,
                })
                for name in row:
                    row[name] += entry[name]
            for rows in set(by_rows) | set(self.local_counts):
                row = by_rows.setdefault(rows, {
                    'keys': 0, 'payload_bytes': 0, 'table_bytes': 0,
                    'shared_duplicate_hits': 0,
                })
                row['local_duplicate_hits'], row['canonicalization_skips'] = self.local_counts.get(rows, (0, 0))
                row['duplicate_hits'] = row['local_duplicate_hits'] + row['shared_duplicate_hits']
                row['candidates'] = row['keys'] + row['duplicate_hits'] + row['canonicalization_skips']
            names = ('keys', 'payload_bytes', 'table_bytes', 'shared_duplicate_hits',
                     'local_duplicate_hits', 'duplicate_hits', 'canonicalization_skips', 'candidates')
            result = {name: sum(row[name] for row in by_rows.values()) for name in names}
            result['groups'] = len(groups)
            result['by_rows'] = dict(sorted(by_rows.items()))
            result['by_key_size'] = groups
            result['duplicate_fraction'] = (result['duplicate_hits'] / result['candidates']
                                            if result['candidates'] else 0.0)
            return result


class SeenManager(BaseManager):
    pass


SeenManager.register('SharedSeen', SharedSeen)
