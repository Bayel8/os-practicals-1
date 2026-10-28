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

condition = threading.Condition()
consumed = []
errors = []


def producer(producer_id):
    global write_pos, count

    for i in range(ITEMS_PER_PRODUCER):
        item = producer_id * ITEMS_PER_PRODUCER + i

        with condition:
            while count == BUFFER_SIZE:
                condition.wait()

            buffer[write_pos] = item
            write_pos = (write_pos + 1) % BUFFER_SIZE
            count += 1

            if not 0 <= count <= BUFFER_SIZE:
                errors.append(f"Ошибка размера буфера: {count}")

            condition.notify_all()


def consumer(consumer_id):
    global read_pos, count

    for _ in range(TOTAL_ITEMS // CONSUMERS):
        with condition:
            while count == 0:
                condition.wait()

            item = buffer[read_pos]
            buffer[read_pos] = None
            read_pos = (read_pos + 1) % BUFFER_SIZE
            count -= 1

            if not 0 <= count <= BUFFER_SIZE:
                errors.append(f"Ошибка размера буфера: {count}")

            condition.notify_all()

        consumed.append(item)


def main():
    threads = []

    for i in range(PRODUCERS):
        threads.append(threading.Thread(target=producer, args=(i,)))

    for i in range(CONSUMERS):
        threads.append(threading.Thread(target=consumer, args=(i,)))

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    actual = Counter(consumed)
    expected = set(range(TOTAL_ITEMS))

    assert not errors, f"Нарушения: {errors}"
    assert len(consumed) == TOTAL_ITEMS, "Неверное количество элементов"
    assert set(consumed) == expected, "Потерянные или лишние элементы"
    assert all(n == 1 for n in actual.values()), "Повторная обработка"
    assert count == 0, "Буфер не пуст"
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
