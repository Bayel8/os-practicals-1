import threading

THREADS = 4
PHASES = 3

barrier = threading.Barrier(THREADS)
print_lock = threading.Lock()


def worker(worker_id):
    for phase in range(1, PHASES + 1):
        with print_lock:
            print(f"Поток {worker_id}: завершил фазу {phase}")

        barrier.wait()

        with print_lock:
            print(f"Поток {worker_id}: прошёл барьер фазы {phase}")


threads = [
    threading.Thread(target=worker, args=(i,))
    for i in range(1, THREADS + 1)
]

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

print("Все 4 потока завершили 3 фазы.")
