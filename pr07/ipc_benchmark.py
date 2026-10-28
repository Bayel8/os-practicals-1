import array
import multiprocessing as mp
import time
from multiprocessing import shared_memory

N = 10_000_000


def expected_checksum():
    return N * (N - 1) // 2


def shared_memory_receiver(name, size, conn):
    shm = shared_memory.SharedMemory(name=name)
    try:
        conn.send("READY")
        conn.recv()  # Ждём, пока родитель запишет массив.

        values = memoryview(shm.buf).cast("q")
        checksum = sum(values)
        del values

        conn.send(checksum)
    finally:
        shm.close()
        conn.close()


def pipe_receiver(conn):
    conn.send("READY")

    payload = conn.recv_bytes()
    values = memoryview(payload).cast("q")
    checksum = sum(values)
    del values

    conn.send(checksum)
    conn.close()


def benchmark_shared_memory(data):
    shm = shared_memory.SharedMemory(create=True, size=len(data) * data.itemsize)
    parent, child = mp.Pipe()

    process = mp.Process(
        target=shared_memory_receiver,
        args=(shm.name, len(data), child),
    )

    try:
        process.start()
        child.close()
        parent.recv()  # Дочерний процесс готов.

        start = time.perf_counter()

        shm.buf[:] = memoryview(data).cast("B")
        parent.send("GO")
        checksum = parent.recv()

        elapsed = time.perf_counter() - start
        process.join()

        if process.exitcode != 0:
            raise RuntimeError("Дочерний процесс завершился с ошибкой")

        return elapsed, checksum
    finally:
        parent.close()
        shm.close()
        shm.unlink()


def benchmark_pipe(data):
    parent, child = mp.Pipe()

    process = mp.Process(target=pipe_receiver, args=(child,))

    try:
        process.start()
        child.close()
        parent.recv()  # Дочерний процесс готов.

        start = time.perf_counter()

        parent.send_bytes(memoryview(data).cast("B"))
        checksum = parent.recv()

        elapsed = time.perf_counter() - start
        process.join()

        if process.exitcode != 0:
            raise RuntimeError("Дочерний процесс завершился с ошибкой")

        return elapsed, checksum
    finally:
        parent.close()


def main():
    print(f"Количество чисел: {N:,}".replace(",", " "))
    print(f"Размер массива: {N * 8 / (1024 ** 2):.2f} MiB")

    print("\nСоздание исходного массива...")
    data = array.array("q", range(N))
    expected = expected_checksum()
    print("Массив создан.")

    for name, benchmark in (
        ("Shared Memory", benchmark_shared_memory),
        ("Pipe", benchmark_pipe),
    ):
        print(f"\nИзмерение: {name}")
        elapsed, checksum = benchmark(data)

        print(f"Время передачи и проверки: {elapsed:.4f} с")
        print(f"Контрольная сумма: {checksum}")
        print(f"Данные корректны: {checksum == expected}")

        if checksum != expected:
            raise RuntimeError(f"Ошибка проверки данных: {name}")

    print("\nВсе проверки завершены.")


if __name__ == "__main__":
    mp.freeze_support()
    main()
