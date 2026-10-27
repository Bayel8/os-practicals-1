#!/usr/bin/env python3

import os
import time


def read_memory(pid):
    result = {}

    try:
        with open(f"/proc/{pid}/smaps_rollup", encoding="utf-8") as file:
            for line in file:
                if line.startswith(("Rss:", "Private_Dirty:", "Shared_Dirty:")):
                    key, value, *_ = line.split()
                    result[key.rstrip(":")] = int(value)
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        pass

    return result


def show_memory(label, pid):
    memory = read_memory(pid)
    print(
        f"{label}: "
        f"RSS={memory.get('Rss', 0)} KiB, "
        f"Private_Dirty={memory.get('Private_Dirty', 0)} KiB, "
        f"Shared_Dirty={memory.get('Shared_Dirty', 0)} KiB",
        flush=True,
    )


def main():
    # Allocate and initialize 50 MiB before fork().
    data = bytearray(50 * 1024 * 1024)
    for index in range(0, len(data), 4096):
        data[index] = 1

    print(f"Parent PID={os.getpid()}", flush=True)
    show_memory("Parent before fork", os.getpid())

    pid = os.fork()

    if pid == 0:
        print(f"Child PID={os.getpid()}", flush=True)
        show_memory("Child before change", os.getpid())

        # Modify each page, causing copy-on-write where needed.
        for index in range(0, len(data), 4096):
            data[index] = 2

        show_memory("Child after change", os.getpid())
        os._exit(0)

    os.waitpid(pid, 0)
    show_memory("Parent after child exits", os.getpid())


if __name__ == "__main__":
    main()
