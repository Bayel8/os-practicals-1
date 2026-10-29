#!/usr/bin/env python3

import threading


class DeadlockDetected(RuntimeError):
    """Исключение при обнаружении цикла ожидания."""


class TrackedLock:
    _guard = threading.RLock()
    _owners = {}
    _waiting = {}
    _names = {}

    def __init__(self, name):
        self.name = name
        self._lock = threading.Lock()
        self._owner = None

    @classmethod
    def _find_path(cls, start, target):
        """Ищет путь в графе ожидания от start до target."""
        stack = [(start, [start])]
        visited = set()

        while stack:
            node, path = stack.pop()

            if node == target:
                return path

            if node in visited:
                continue

            visited.add(node)

            next_node = cls._waiting.get(node)
            if next_node is not None:
                stack.append((next_node, path + [next_node]))

        return None

    def acquire(self):
        tid = threading.get_ident()

        with self._guard:
            self._names[tid] = threading.current_thread().name

            owner = self._owners.get(self.name)

            if owner == tid:
                raise RuntimeError(
                    f"Повторный захват нерекурсивной блокировки {self.name}"
                )

            if owner is not None:
                # Добавляем ребро: текущий поток ждёт владельца.
                self._waiting[tid] = owner

                path = self._find_path(owner, tid)

                if path is not None:
                    del self._waiting[tid]
                    cycle = [tid] + path
                    labels = [
                        self._names.get(item, str(item))
                        for item in cycle
                    ]

                    raise DeadlockDetected(
                        "Обнаружен цикл ожидания: " + " -> ".join(labels)
                    )

        try:
            self._lock.acquire()
        except BaseException:
            with self._guard:
                self._waiting.pop(tid, None)
            raise

        with self._guard:
            self._waiting.pop(tid, None)
            self._owners[self.name] = tid
            self._owner = tid

        return True

    def release(self):
        tid = threading.get_ident()

        with self._guard:
            if self._owner != tid:
                raise RuntimeError(
                    f"Поток не владеет блокировкой {self.name}"
                )

            self._owner = None
            self._owners.pop(self.name, None)

        self._lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
        return False
