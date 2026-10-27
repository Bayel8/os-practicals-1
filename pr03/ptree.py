#!/usr/bin/env python3

import os
from pathlib import Path

PROC = Path("/proc")


def read_process(pid):
    """Read process information from /proc."""
    try:
        status = (PROC / str(pid) / "status").read_text()
        info = {}

        for line in status.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                info[key] = value.strip()

        uid = int(info["Uid"].split()[0])
        if uid != os.getuid():
            return None

        stat = (PROC / str(pid) / "stat").read_text()
        # The command name can contain spaces and parentheses.
        # Split after the final ')' to parse the remaining fields safely.
        fields = stat[stat.rfind(")") + 2:].split()

        state = fields[0]
        ppid = int(fields[1])
        rss_kb = int(info.get("VmRSS", "0 kB").split()[0])

        return {
            "pid": pid,
            "ppid": ppid,
            "state": state,
            "rss_kb": rss_kb,
        }

    except (OSError, ValueError, KeyError, IndexError):
        # The process may exit while /proc is being read.
        return None


def main():
    processes = {}

    for entry in PROC.iterdir():
        if entry.name.isdigit():
            process = read_process(int(entry.name))
            if process is not None:
                processes[process["pid"]] = process

    children = {pid: [] for pid in processes}

    for pid, process in processes.items():
        parent = process["ppid"]
        if parent in children and parent != pid:
            children[parent].append(pid)

    for pid in children:
        children[pid].sort()

    roots = sorted(
        pid for pid, process in processes.items()
        if process["ppid"] not in processes
    )

    print(f"{'PID':>7} {'STATE':<7} {'RSS (MiB)':>10}")
    visited = set()

    def print_tree(pid, prefix="", is_last=True):
        if pid in visited:
            return

        visited.add(pid)
        process = processes[pid]
        branch = "└── " if is_last else "├── "

        print(
            f"{prefix}{branch}{process['pid']:>7} "
            f"{process['state']:<7} "
            f"{process['rss_kb'] / 1024:>10.2f}"
        )

        child_prefix = prefix + ("    " if is_last else "│   ")
        child_pids = children[pid]

        for index, child_pid in enumerate(child_pids):
            print_tree(
                child_pid,
                child_prefix,
                index == len(child_pids) - 1,
            )

    for root in roots:
        if root not in visited:
            process = processes[root]
            print(
                f"{process['pid']:>7} "
                f"{process['state']:<7} "
                f"{process['rss_kb'] / 1024:>10.2f}"
            )
            visited.add(root)

            for index, child_pid in enumerate(children[root]):
                print_tree(
                    child_pid,
                    "",
                    index == len(children[root]) - 1,
                )

    # Include any processes missed because of a race while reading /proc.
    for pid in sorted(processes):
        if pid not in visited:
            print_tree(pid)


if __name__ == "__main__":
    main()
