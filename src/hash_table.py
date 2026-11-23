"""String-key hash tables using Horner hashing."""

import math
from typing import TypeAlias


_Value: TypeAlias = object
_MISSING = object()
_TOMBSTONE = object()


class _Entry:
    def __init__(self, key: str, value: _Value, next_entry: "_Entry | None" = None):
        self.key = key
        self.value = value
        self.next = next_entry


class _HashTableBase:
    def __init__(
        self,
        initial_capacity: int = 8,
        max_load_factor: float = 0.75,
        auto_resize: bool = True,
    ):
        if (
            isinstance(initial_capacity, bool)
            or not isinstance(initial_capacity, int)
            or initial_capacity <= 0
        ):
            raise ValueError("initial_capacity must be a positive integer")
        if (
            isinstance(max_load_factor, bool)
            or not isinstance(max_load_factor, (int, float))
            or not math.isfinite(max_load_factor)
            or not 0 < max_load_factor <= 1
        ):
            raise ValueError("max_load_factor must be greater than 0 and at most 1")
        if not isinstance(auto_resize, bool):
            raise ValueError("auto_resize must be a bool")

        self._capacity = initial_capacity
        self._max_load_factor = float(max_load_factor)
        self._auto_resize = auto_resize
        self._size = 0
        self.last_probes = 0

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def load_factor(self) -> float:
        return self._size / self._capacity

    @property
    def max_load_factor(self) -> float:
        return self._max_load_factor

    @property
    def auto_resize(self) -> bool:
        return self._auto_resize

    def __len__(self) -> int:
        return self._size

    def _hash_details(self, key: str) -> tuple[int, tuple[int, ...]]:
        if not isinstance(key, str):
            raise TypeError("keys must be strings")
        value = 0
        trace = []
        for character in key:
            value = (31 * value + ord(character)) % self._capacity
            trace.append(value)
        return value, tuple(trace)

    def _needs_resize(self) -> bool:
        return (
            self._auto_resize
            and (self._size + 1) / self._capacity > self._max_load_factor
        )

    def _resize(self) -> None:
        raise NotImplementedError

    def get(self, key: str, default: _Value = None) -> _Value:
        raise NotImplementedError

    def put(self, key: str, value: _Value) -> None:
        raise NotImplementedError

    def contains(self, key: str) -> bool:
        raise NotImplementedError

    def delete(self, key: str) -> bool:
        raise NotImplementedError

    def debug_slots(self) -> list[tuple[int, tuple[str, ...]]]:
        raise NotImplementedError


class ChainingHashTable(_HashTableBase):
    """Hash table with a linked list in each bucket."""

    def __init__(
        self,
        initial_capacity: int = 8,
        max_load_factor: float = 0.75,
        auto_resize: bool = True,
    ):
        super().__init__(initial_capacity, max_load_factor, auto_resize)
        self._buckets: list[_Entry | None] = [None] * self._capacity

    def _find(self, key: str) -> tuple[int, _Entry | None]:
        index, _ = self._hash_details(key)
        probes = 0
        entry = self._buckets[index]
        while entry is not None:
            probes += 1
            if entry.key == key:
                self.last_probes = probes
                return index, entry
            entry = entry.next
        self.last_probes = probes
        return index, None

    def get(self, key: str, default: _Value = None) -> _Value:
        _, entry = self._find(key)
        return default if entry is None else entry.value

    def put(self, key: str, value: _Value) -> None:
        index, entry = self._find(key)
        if entry is not None:
            entry.value = value
            return

        if self._needs_resize():
            self._resize()
            index, _ = self._hash_details(key)
        entry = _Entry(key, value)
        if self._buckets[index] is None:
            self._buckets[index] = entry
        else:
            tail = self._buckets[index]
            while tail.next is not None:
                tail = tail.next
            tail.next = entry
        self._size += 1

    def contains(self, key: str) -> bool:
        _, entry = self._find(key)
        return entry is not None

    def delete(self, key: str) -> bool:
        index, _ = self._hash_details(key)
        previous = None
        entry = self._buckets[index]
        probes = 0
        while entry is not None:
            probes += 1
            if entry.key == key:
                if previous is None:
                    self._buckets[index] = entry.next
                else:
                    previous.next = entry.next
                self._size -= 1
                self.last_probes = probes
                return True
            previous = entry
            entry = entry.next
        self.last_probes = probes
        return False

    def _resize(self) -> None:
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = [None] * self._capacity
        for head in old_buckets:
            entry = head
            while entry is not None:
                index, _ = self._hash_details(entry.key)
                self._buckets[index] = _Entry(
                    entry.key, entry.value, self._buckets[index]
                )
                entry = entry.next

    def debug_slots(self) -> list[tuple[int, tuple[str, ...]]]:
        slots = []
        for index, head in enumerate(self._buckets):
            details = []
            position = 0
            entry = head
            while entry is not None:
                position += 1
                _, trace = self._hash_details(entry.key)
                details.append(
                    f"{entry.key!r} -> {entry.value!r}; "
                    f"Horner trace={trace}; start={index}; "
                    f"chain position={position}; comparisons={position}"
                )
                entry = entry.next
            slots.append((index, tuple(details) if details else ("(empty)",)))
        return slots


class LinearProbingHashTable(_HashTableBase):
    """Hash table using linear probing and tombstones for deletion."""

    def __init__(
        self,
        initial_capacity: int = 8,
        max_load_factor: float = 0.75,
        auto_resize: bool = True,
    ):
        super().__init__(initial_capacity, max_load_factor, auto_resize)
        self._slots: list[_Entry | object | None] = [None] * self._capacity

    def _find_index(self, key: str) -> int | None:
        index, _ = self._hash_details(key)
        probes = 0
        for _ in range(self._capacity):
            probes += 1
            entry = self._slots[index]
            if entry is None:
                self.last_probes = probes
                return None
            if entry is not _TOMBSTONE and entry.key == key:
                self.last_probes = probes
                return index
            index = (index + 1) % self._capacity
        self.last_probes = probes
        return None

    def _insertion_index(self, key: str) -> int | None:
        index, _ = self._hash_details(key)
        first_tombstone = None
        for _ in range(self._capacity):
            entry = self._slots[index]
            if entry is None:
                return first_tombstone if first_tombstone is not None else index
            if entry is _TOMBSTONE and first_tombstone is None:
                first_tombstone = index
            index = (index + 1) % self._capacity
        return first_tombstone

    def get(self, key: str, default: _Value = None) -> _Value:
        index = self._find_index(key)
        if index is None:
            return default
        entry = self._slots[index]
        return entry.value

    def put(self, key: str, value: _Value) -> None:
        if not isinstance(key, str):
            raise TypeError("keys must be strings")
        existing_index = self._find_index(key)
        if existing_index is not None:
            self._slots[existing_index].value = value
            return

        if self._needs_resize():
            self._resize()
        insertion_index = self._insertion_index(key)
        if insertion_index is None:
            raise OverflowError("fixed-size hash table has no empty slot")
        self._slots[insertion_index] = _Entry(key, value)
        self._size += 1

    def contains(self, key: str) -> bool:
        return self._find_index(key) is not None

    def delete(self, key: str) -> bool:
        index = self._find_index(key)
        if index is None:
            return False
        self._slots[index] = _TOMBSTONE
        self._size -= 1
        return True

    def _resize(self) -> None:
        old_slots = self._slots
        self._capacity *= 2
        self._slots = [None] * self._capacity
        self._size = 0
        for entry in old_slots:
            if entry is not None and entry is not _TOMBSTONE:
                index = self._insertion_index(entry.key)
                self._slots[index] = _Entry(entry.key, entry.value)
                self._size += 1

    def debug_slots(self) -> list[tuple[int, tuple[str, ...]]]:
        slots = []
        for index, entry in enumerate(self._slots):
            if entry is None:
                details = ("(empty)",)
            elif entry is _TOMBSTONE:
                details = ("(tombstone)",)
            else:
                start, trace = self._hash_details(entry.key)
                path = []
                probe_index = start
                for _ in range(self._capacity):
                    path.append(probe_index)
                    if probe_index == index:
                        break
                    probe_index = (probe_index + 1) % self._capacity
                details = (
                    f"{entry.key!r} -> {entry.value!r}; Horner trace={trace}; "
                    f"start={start}; probe path={tuple(path)}",
                )
            slots.append((index, details))
        return slots


HashTable = ChainingHashTable
