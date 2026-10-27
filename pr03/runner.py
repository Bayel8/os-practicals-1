#!/usr/bin/env python3

import os
import sys
import time


def main():
    if len(sys.argv) < 3:
        print(
            f"Usage: {sys.argv[0]} N COMMAND [ARG ...]",
            file=sys.stderr,
        )
        return 2

    try:
        n = int(sys.argv[1])
        if n < 1:
            raise ValueError
    except ValueError:
        print("Error: N must be a positive integer.", file=sys.stderr)
        return 2

    command = sys.argv[2:]
    start_times = {}
    exit_codes = []
    created_pids = []

    print(f"Starting {n} child processes: {' '.join(command)}", flush=True)

    try:
        for _ in range(n):
            start_time = time.monotonic()

            try:
                pid = os.fork()
            except OSError as error:
                print(f"fork failed: {error}", file=sys.stderr)
                break

            if pid == 0:
                # Child process: replace itself with the requested command.
                try:
                    os.execvp(command[0], command)
                except OSError as error:
                    print(
                        f"exec failed for {command[0]}: {error}",
                        file=sys.stderr,
                    )
                    os._exit(127)

            # Parent process: remember this child's start time.
            start_times[pid] = start_time
            created_pids.append(pid)

    finally:
        # Reap every child that was successfully created.
        for _ in created_pids:
            try:
                pid, status = os.wait()
            except InterruptedError:
                continue
            except ChildProcessError:
                print("No remaining child processes.", file=sys.stderr)
                break

            elapsed = time.monotonic() - start_times[pid]
            exit_code = os.waitstatus_to_exitcode(status)
            exit_codes.append(exit_code)

            print(
                f"PID={pid} "
                f"exit_code={exit_code} "
                f"elapsed={elapsed:.3f}s"
            )

    if any(exit_code != 0 for exit_code in exit_codes):
        return 1

    return 0 if len(created_pids) == n else 1

if __name__ == "__main__":
    sys.exit(main())
