#!/usr/bin/env python3

import threading

from tracked_lock import TrackedLock, DeadlockDetected


lock_a = TrackedLock("A")
lock_b = TrackedLock("B")

barrier = threading.Barrier(2)


def worker(name, first_lock, second_lock):
    acquired_second = False

    first_lock.acquire()
    print(f"{name}: захватил {first_lock.name}")

    try:
        # Оба потока сначала захватывают свои первые блокировки.
        barrier.wait(timeout=5)

        print(f"{name}: пытается захватить {second_lock.name}")

        second_lock.acquire()
        acquired_second = True

        print(f"{name}: захватил {second_lock.name}")

    except DeadlockDetected as error:
        print(f"{name}: {error}")

    except threading.BrokenBarrierError:
        print(f"{name}: ошибка синхронизации потоков")

    finally:
        if acquired_second:
            second_lock.release()

        first_lock.release()
        print(f"{name}: освободил свои блокировки")


def main():
    thread_a = threading.Thread(
        target=worker,
        args=("Thread-A", lock_a, lock_b),
        name="Thread-A",
    )

    thread_b = threading.Thread(
        target=worker,
        args=("Thread-B", lock_b, lock_a),
        name="Thread-B",
    )

    thread_a.start()
    thread_b.start()

    thread_a.join(timeout=10)
    thread_b.join(timeout=10)

    if thread_a.is_alive() or thread_b.is_alive():
        print("ОШИБКА: потоки не завершились вовремя")
    else:
        print("Проверка завершена: оба потока остановлены")


if __name__ == "__main__":
    main()
