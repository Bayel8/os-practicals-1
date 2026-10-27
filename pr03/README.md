
# Practical Work 3: Processes in Linux

## Objective

Study Linux process management, process creation, process states, parent-child relationships, and Copy-on-Write memory behavior.

## Environment

- OS: Ubuntu on WSL2
- Python: 3.10
- Source of process information: `/proc`

## Files

### 1. `ptree.py` — Process Tree

Reads process information from `/proc`, filters processes owned by the current user, and displays a process tree with PID, state, and RSS memory usage.

Run:

```bash
python3 ptree.py
```

### 2. `runner.py` — Process Runner

Creates N child processes using `fork()`. Each child replaces itself with the requested command using `execvp()`. The parent waits for each child and reports its exit code and elapsed time.

Successful example:

```bash
python3 runner.py 3 sleep 1
```

Expected result: three child processes finish with exit code 0 after approximately one second.

Error example:

```bash
python3 runner.py 2 command_that_does_not_exist
```

Expected result: each child reports exit code 127 because the command cannot be found. The runner returns a non-zero status.

### 3. `zombie.py` — Zombie Process

Creates a child process that exits before its parent collects the exit status. The parent temporarily delays calling `waitpid()`, allowing the child to appear as a zombie.

Run:

```bash
python3 zombie.py
```

While the parent is waiting, inspect the child from another terminal:

```bash
ps -o pid,ppid,state,stat,cmd -p CHILD_PID
```

A state of `Z` and the text `<defunct>` indicate a zombie process.

The parent eventually calls `waitpid()` to reap the child.

### 4. `orphan.py` — Orphan Process

Creates a child process and exits the parent first. The child prints its original and new parent PIDs.

Run:

```bash
python3 orphan.py
```

The child's PPID changes after the original parent exits. In this WSL environment, the child was adopted by PID 308. Orphan adoption depends on the system's process hierarchy and available subreapers; it is not always PID 1.

### 5. `cow.py` — Copy-on-Write

Allocates and initializes a 50 MiB byte array before `fork()`. The child measures memory usage, modifies one byte on each memory page, and measures memory again.

Run:

```bash
python3 cow.py
```

The experiment reads RSS, Private_Dirty, and Shared_Dirty from `/proc/PID/smaps_rollup`.

Observed child measurements:

| Metric | Before modification | After modification |
|---|---:|---:|
| RSS | 57064 KiB | 57200 KiB |
| Private_Dirty | 456 KiB | 51736 KiB |
| Shared_Dirty | 54124 KiB | 2852 KiB |

The increase in Private_Dirty and decrease in Shared_Dirty demonstrate that modified pages become private through Copy-on-Write. RSS does not necessarily increase by the full allocated amount because it includes resident pages regardless of whether they are shared or private.

## Control Questions

### 1. Why does `fork()` return different values?

`fork()` returns 0 in the child process, the child's PID in the parent process, and -1 on failure. This allows the parent and child to execute different code paths.

### 2. What happens if `exec()` is called without `fork()`?

The current process is replaced by the new program. It does not create a separate child process, and the original program does not continue after a successful `exec()`.

## Conclusion

The practical work demonstrates process-tree inspection through `/proc`, process creation and execution, child-process cleanup, zombie and orphan behavior, and Copy-on-Write memory accounting.
