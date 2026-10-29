#!/usr/bin/env python3

import argparse
import threading
import time


def run_philosophers(mode, duration=5, count=5):
    forks = [threading.Lock() for _ in range(count)]
    meals = [0] * count
    stop = threading.Event()

    # Для режима limit одновременно допускаем не более N-1 философов.
    room = threading.Semaphore(count - 1)

    # Синхронизация нужна только для воспроизводимого deadlock.
    barrier = threading.Barrier(count) if mode == "deadlock" else None

    def philosopher(i):
        left = i
        right = (i + 1) % count

        while not stop.is_set():
            if mode == "limit":
                room.acquire()

            if mode == "ordered":
                first, second = sorted((left, right))
            else:
                first, second = left, right

            got_first = False
            got_second = False

            try:
                forks[first].acquire()
                got_first = True

                if mode == "deadlock":
                    # Все философы берут по одной вилке до попытки
                    # получить вторую. Так deadlock воспроизводится
                    # детерминированно.
                    barrier.wait(timeout=3)

                if stop.is_set() and mode != "deadlock":
                    continue

                forks[second].acquire()
                got_second = True

                meals[i] += 1

            except threading.BrokenBarrierError:
                return

            finally:
                if got_second:
                    forks[second].release()
                if got_first:
                    forks[first].release()
                if mode == "limit":
                    room.release()

            if mode != "deadlock":
                time.sleep(0.001)

    threads = [
        threading.Thread(
            target=philosopher,
            args=(i,),
            name=f"P{i}",
            daemon=(mode == "deadlock"),
        )
        for i in range(count)
    ]

    started = time.monotonic()

    for thread in threads:
        thread.start()

    if mode == "deadlock":
        # Даём всем потокам возможность застрять на второй вилке.
        time.sleep(1)
        elapsed = time.monotonic() - started
        print("Наивный режим: проверяем состояние потоков")
        for thread in threads:
            print(f"{thread.name}: {'заблокирован' if thread.is_alive() else 'завершён'}")
    else:
        time.sleep(duration)
        stop.set()

        for thread in threads:
            thread.join(timeout=2)

        elapsed = time.monotonic() - started

    print(f"\nРежим: {mode}")
    print(f"Время наблюдения: {elapsed:.2f} с")
    print("Количество приёмов пищи:")
    for i, total in enumerate(meals):
        print(f"P{i}: {total}")

    print("Всего приёмов пищи:", sum(meals))


def main():
    parser = argparse.ArgumentParser(
        description="Задача обедающих философов"
    )
    parser.add_argument(
        "mode",
        choices=["deadlock", "ordered", "limit"],
        help="Режим решения",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5,
        help="Время работы исправленных режимов в секундах",
    )
    args = parser.parse_args()

    run_philosophers(args.mode, args.duration)


if __name__ == "__main__":
    main()
