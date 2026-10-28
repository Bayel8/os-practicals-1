import statistics
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from functools import partial
from pathlib import Path
from urllib.request import urlopen

WORKERS = 4
REPEATS = 3
URL_COUNT = 20


def fetch_url(url):
    with urlopen(url, timeout=10) as response:
        return len(response.read())


def sequential(urls):
    return [fetch_url(url) for url in urls]


def threaded(urls):
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        return list(executor.map(fetch_url, urls))


def processed(urls):
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        return list(executor.map(fetch_url, urls))


def benchmark(name, function, urls):
    times = []

    print(f"\n{name}")

    for run in range(1, REPEATS + 1):
        start = time.perf_counter()
        results = function(urls)
        elapsed = time.perf_counter() - start

        if len(results) != URL_COUNT or any(size <= 0 for size in results):
            raise RuntimeError("Не все URL загружены корректно")

        times.append(elapsed)
        print(f"  Запуск {run}: {elapsed:.4f} с")

    median = statistics.median(times)
    print(f"  Медиана: {median:.4f} с")
    return median


def main():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)

        for i in range(URL_COUNT):
            (root / f"page{i}.txt").write_text(
                f"Локальная тестовая страница номер {i}\n",
                encoding="utf-8",
            )

        handler = partial(SimpleHTTPRequestHandler, directory=str(root))
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        server_thread = threading.Thread(
            target=server.serve_forever,
            daemon=True,
        )
        server_thread.start()

        try:
            port = server.server_address[1]
            urls = [
                f"http://127.0.0.1:{port}/page{i}.txt"
                for i in range(URL_COUNT)
            ]

            print(f"URL: {URL_COUNT}")
            print(f"Рабочих потоков/процессов: {WORKERS}")
            print(f"Повторов: {REPEATS}")
            print("Сервер: локальный HTTP")

            results = {
                "Последовательно": benchmark("Последовательно", sequential, urls),
                "4 потока": benchmark("ThreadPoolExecutor", threaded, urls),
                "4 процесса": benchmark("ProcessPoolExecutor", processed, urls),
            }

            baseline = results["Последовательно"]

            print("\nИТОГОВАЯ ТАБЛИЦА")
            print(f"{'Способ':<25} {'Медиана, с':>12} {'Ускорение':>12}")

            for name, median in results.items():
                print(f"{name:<25} {median:>12.4f} {baseline / median:>11.2f}x")

        finally:
            server.shutdown()
            server.server_close()
            server_thread.join()


if __name__ == "__main__":
    main()
