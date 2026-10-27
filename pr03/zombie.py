
#!/usr/bin/env python3

import os
import time


def main():
    pid = os.fork()

    if pid == 0:
        # Child exits immediately.
        print(f"Child PID={os.getpid()} exiting.", flush=True)
        os._exit(0)

    # Parent deliberately does not wait immediately.
    print(f"Parent PID={os.getpid()}", flush=True)
    print(f"Child PID={pid}", flush=True)

    try:
        time.sleep(15)

        status_path = f"/proc/{pid}/status"
        try:
            with open(status_path, encoding="utf-8") as file:
                for line in file:
                    if line.startswith(("Name:", "State:", "Pid:", "PPid:")):
                        print(line, end="")
        except FileNotFoundError:
            print("Child process no longer exists.")

        print("\nWaiting for child to finish cleanup...", flush=True)
    finally:
        # Reap the child so no zombie is left behind.
        os.waitpid(pid, 0)
        print("Child reaped. No zombie left by this script.", flush=True)


if __name__ == "__main__":
    main()
