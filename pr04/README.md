# Practical Work No. 4: Threads and Processes

## 1. Objective

The objective of this practical work is to study multithreading and multiprocessing in Python, compare their performance for CPU-bound and I/O-bound tasks, and demonstrate the differences between shared thread memory and separate process memory.

## 2. Environment

- Operating system: Ubuntu on WSL
- Python version: 3.10.12
- Available processors (`nproc`): 12
- Number of workers: 4
- Repetitions per benchmark: 3
- Performance metric: median execution time

## 3. Project Structure

- `generate_numbers.py` - generates a file containing 10,000,000 integers.
- `benchmark_sum.py` - compares sequential summation, four threads, and four processes.
- `benchmark_network.py` - compares sequential downloading, `ThreadPoolExecutor`, and `ProcessPoolExecutor` using 20 URLs served by a local HTTP server.
- `memory_demo.py` - demonstrates memory sharing between threads and memory isolation between processes.
- `sum_results.txt` - recorded results for the CPU-bound task.
- `network_results.txt` - recorded results for the network task.
- `.gitignore` - excludes the generated `numbers.txt` file, `__pycache__/`, and `.pyc` files.

## 4. CPU-Bound Task: Summing 10 Million Integers

The program calculated the sum of integers from 1 to 10,000,000.

Expected result:

`50,000,005,000,000`

All three methods produced the correct result.

### Results

| Method | Median time (s) | Speedup |
|---|---:|---:|
| Sequential execution | 0.374 | 1.00x |
| 4 threads (`threading`) | 0.424 | 0.88x |
| 4 processes (`multiprocessing`) | 0.154 | 2.42x |

### Analysis

The four-thread implementation was slower than sequential execution: 0.424 seconds compared with 0.374 seconds.

In standard CPython, the Global Interpreter Lock (GIL) prevents multiple threads from executing Python bytecode simultaneously within the same interpreter. As a result, CPU-bound Python code generally does not become faster simply by adding threads. Thread management also introduces overhead.

The four-process implementation completed the task in 0.154 seconds, achieving approximately 2.42x speedup. Separate processes can execute Python code in parallel across multiple CPU cores. However, multiprocessing introduces additional overhead for process creation, memory management, and communication.

## 5. Network Task: Downloading 20 URLs

The network experiment used 20 URLs served by a local HTTP server. Three execution strategies were compared:

1. Sequential downloading.
2. Concurrent downloading with `ThreadPoolExecutor`.
3. Concurrent downloading with `ProcessPoolExecutor`.

### Results

| Method | Median time (s) | Speedup |
|---|---:|---:|
| Sequential execution | 0.0154 | 1.00x |
| `ThreadPoolExecutor` | 0.0278 | 0.55x |
| `ProcessPoolExecutor` | 0.0317 | 0.49x |

### Analysis

Sequential downloading was the fastest method in this experiment. The server was running locally, and the responses were small, so network waiting time was minimal. The overhead of creating and managing concurrent tasks exceeded the potential performance benefit.

For real network requests with significant waiting time, threads can improve performance because one thread can wait for a response while other threads handle different requests. Processes are generally less suitable for simple I/O-bound tasks because they require additional resources.

These results apply to the local test environment and should not be interpreted as proof that multithreading is always slower for network operations.

## 6. Memory Demonstration

The `memory_demo.py` program produced the following output:

```text
After thread modification: ['parent', 'thread']
In child process: ['parent', 'process']
In parent process: ['parent']
```

The thread modified a shared list, and the change was visible in the main thread. Threads belonging to the same process share the same address space.

The child process modified its own copy of the list. This change was not visible in the parent process. Ordinary Python objects are not automatically shared as mutable memory between separate processes.

## 7. Answers to Control Questions

### 1. Which properties do threads in the same process share, and which are different?

Threads share the process's address space, global variables, heap memory, and open file resources. Each thread has its own execution stack, program counter, and CPU register state. Threads can communicate through shared objects, but synchronization may be necessary to avoid race conditions.

### 2. Why do Python threads usually not speed up CPU-bound tasks in CPython, while processes can?

The GIL allows only one thread at a time to execute Python bytecode in a standard CPython interpreter. Therefore, CPU-bound threads usually cannot use multiple CPU cores for Python bytecode execution simultaneously.

Separate processes have separate Python interpreters and GILs. They can run in parallel on different CPU cores, which can improve CPU-bound performance.

### 3. When should threads or processes be used?

- **Threads:** Suitable for I/O-bound tasks, such as network requests, file operations, and waiting for external services.
- **Processes:** Suitable for CPU-bound tasks, such as numerical calculations and computationally intensive data processing.
- **Sequential execution:** Often suitable for small tasks where parallelization overhead is greater than the potential benefit.

## 8. How to Run

Run these commands from the `pr04` directory.

Generate the input data:

```bash
python3 generate_numbers.py
```

Run the CPU benchmark:

```bash
python3 benchmark_sum.py
```

Save the CPU benchmark output:

```bash
python3 benchmark_sum.py | tee sum_results.txt
```

Run the network benchmark and save its output:

```bash
python3 benchmark_network.py | tee network_results.txt
```

Run the memory demonstration:

```bash
python3 memory_demo.py
```

Check the available processor count:

```bash
nproc
```

The `numbers.txt` file is generated locally and excluded from Git because it is a large input file.

## 9. Conclusion

This practical work demonstrated the differences between Python threads and processes.

The CPU-bound benchmark showed that four threads were slower than sequential execution, while four processes achieved approximately 2.42x speedup. This is consistent with the GIL's limitations in standard CPython and the ability of separate processes to execute in parallel.

In the local network benchmark, sequential execution was faster because the requests completed quickly and concurrent execution introduced additional overhead. Threads can still be useful for I/O-bound tasks when network waiting time is significant.

The memory demonstration confirmed that threads share the process address space, while changes to ordinary mutable objects in a child process do not automatically affect the parent process.

Overall, the appropriate execution strategy depends on the workload, the cost of parallelization, and whether the task is CPU-bound or I/O-bound.
