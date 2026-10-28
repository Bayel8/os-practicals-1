import threading
from collections import Counter

BUFFER_SIZE = 5
PRODUCERS = 3
CONSUMERS = 2
ITEMS_PER_PRODUCER = 1000
TOTAL_ITEMS = PRODUCERS * ITEMS_PER_PRODUCER

buffer = [None] * BUFFER_SIZE
write_pos = 0
read_pos = 0
count = 0

empty = threading.Semaphore(BUFFER_SIZE)
full = threading.Semaphore(0)
mutex = threading.Lock()

consumed = []
results_lock = threading.Lock()
errors = []


def producer(producer_id):
    global write_pos, count

    for i in range(ITEMS_PER_PRODUCER):
        item = producer_id * ITEMS_PER_PRODUCER + i

        empty.acquire()
        with mutex:
            if count >= BUFFER_SIZE:
                errors.append("ОШИБКА: переполнение буфера")

            buffer[write_pos] = item
            write_pos = (write_pos + 1) % BUFFER_SIZE
            count += 1

            if not 0 <= count <= BUFFER_SIZE:
                errors.append(f"Некорректное число элементов: {count}")

        full.release()


def consumer(consumer_id):
    global read_pos, count

    # Всего 3000 элементов, поэтому каждый потребитель
    # обрабатывает ровно половину.
    items_to_consume = TOTAL_ITEMS // CONSUMERS

    for _ in range(items_to_consume):
        full.acquire()
        with mutex:
            if count <= 0:
                errors.append("ОШИБКА: попытка чтения пустого буфера")

            item = buffer[read_pos]
            buffer[read_pos] = None
            read_pos = (read_pos + 1) % BUFFER_SIZE
            count -= 1

            if not 0 <= count <= BUFFER_SIZE:
                errors.append(f"Некорректное число элементов: {count}")

        empty.release()

        with results_lock:
            consumed.append(item)


def main():
    threads = []

    for producer_id in range(PRODUCERS):
        threads.append(
            threading.Thread(target=producer, args=(producer_id,))
        )

    for consumer_id in range(CONSUMERS):
        threads.append(
            threading.Thread(target=consumer, args=(consumer_id,))
        )

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    expected = set(range(TOTAL_ITEMS))
    actual = Counter(consumed)

    assert not errors, f"Нарушения: {errors}"
    assert len(consumed) == TOTAL_ITEMS, "Неверное число обработанных элементов"
    assert set(consumed) == expected, "Потеряны или появились лишние элементы"
    assert all(n == 1 for n in actual.values()), "Элемент обработан больше одного раза"
    assert count == 0, "Буфер не пуст после завершения"
    assert all(item is None for item in buffer), "В буфере остались элементы"

    print("Результат: SUCCESS")
    print(f"Производителей: {PRODUCERS}")
    print(f"Потребителей: {CONSUMERS}")
    print(f"Размер буфера: {BUFFER_SIZE}")
    print(f"Создано элементов: {TOTAL_ITEMS}")
    print(f"Обработано элементов: {len(consumed)}")
    print(f"Повторных обработок: {sum(n - 1 for n in actual.values())}")
    print(f"Нарушений инвариантов: {len(errors)}")
    print(f"Элементов в буфере после завершения: {count}")


if __name__ == "__main__":
    main()
