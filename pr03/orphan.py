#!/usr/bin/env python3

import os
import time


def main():
    pid = os.fork()

    if pid == 0:
        # Child process
        original_parent = os.getppid()

        print(f"Child PID={os.getpid()}", flush=True)
        print(f"Original PPID={original_parent}", flush=True)

        time.sleep(2)

        new_parent = os.getppid()
        print(f"New PPID={new_parent}", flush=True)

        time.sleep(3)
        os._exit(0)

    # Parent process exits before the child.
    print(f"Parent PID={os.getpid()}", flush=True)
    print(f"Child PID={pid}", flush=True)
    os._exit(0)


if __name__ == "__main__":
    main()
