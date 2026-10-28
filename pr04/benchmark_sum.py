import statistics
import time
from array import array
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path

DATA_FILE = Path(__file__).parent / "numbers.txt"
WORKERS = 4
REPEATS = 3
EXPECTED_SUM = 50_000_005_000_000

# Глобальный массив доступен рабочим потокам и,
# при использовании fork в Linux, дочерним процессам.
DATA = array("Q")


def load_data():
    """Загружает числа до начала измерений."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        DATA.extend(map(int, file))

    print(f"Загружено чисел: {len(DATA):,}")
    print(f"Размер массива: {len(DATA) * DATA.itemsize / 1024**2:.1f} MiB")


def sum_range(start, end):
    """Суммирует часть массива."""
    total = 0
    for index in range(start, end):
        total += DATA[index]
    return total


def make_chunks():
    """Разделяет массив на четыре непересекающиеся части."""
    size = len(DATA)
    return [
        (size * i // WORKERS, size * (i + 1) // WORKERS)
        for i in range(WORKERS)
    ]


def sequential_sum():
    return sum_range(0, len(DATA))


def threaded_sum():
    chunks = make_chunks()
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        results = executor.map(lambda_bounds, chunks)
        return sum(results)


def lambda_bounds(bounds):
    return sum_range(*bounds)


def process_sum():
    chunks = make_chunks()
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        results = executor.map(sum_range, *zip(*chunks))
        return sum(results)


def benchmark(name, function):
    times = []

    print(f"\n{name}")

    for run in range(1, REPEATS + 1):
        start = time.perf_counter()
        result = function()
        elapsed = time.perf_counter() - start

        if result != EXPECTED_SUM:
            raise ValueError(
                f"Неверная сумма: {result}; ожидалось {EXPECTED_SUM}"
            )

        times.append(elapsed)
        print(f"  Запуск {run}: {elapsed:.3f} с; сумма = {result}")

    median = statistics.median(times)
    print(f"  Медиана: {median:.3f} с")

    return median


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"Не найден файл {DATA_FILE}. "
            "Сначала запусти generate_numbers.py"
        )

    load_data()

    print(f"Доступные процессоры (nproc): {__import__('os').cpu_count()}")
    print(f"Рабочих потоков/процессов: {WORKERS}")
    print(f"Повторов каждого теста: {REPEATS}")

    results = {
        "Один поток": benchmark("Один поток", sequential_sum),
        "4 потока": benchmark("4 потока (threading)", threaded_sum),
        "4 процесса": benchmark("4 процесса (multiprocessing)", process_sum),
    }

    baseline = results["Один поток"]

    print("\nИТОГОВАЯ ТАБЛИЦА")
    print(f"{'Способ':<25} {'Медиана, с':>12} {'Ускорение':>12}")

    for name, median in results.items():
        print(f"{name:<25} {median:>12.3f} {baseline / median:>11.2f}x")


if __name__ == "__main__":
    main()
