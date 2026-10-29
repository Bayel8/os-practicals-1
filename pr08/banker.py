#!/usr/bin/env python3

import sys


def load_state(filename):
    with open(filename, "r", encoding="utf-8") as file:
        lines = [
            line.strip()
            for line in file
            if line.strip()
        ]

    n, m = map(int, lines[0].split())
    available = list(map(int, lines[1].split()))

    allocation = [
        list(map(int, lines[i].split()))
        for i in range(2, 2 + n)
    ]

    maximum = [
        list(map(int, lines[i].split()))
        for i in range(2 + n, 2 + 2 * n)
    ]

    if len(available) != m:
        raise ValueError("Неверная длина Available")

    if any(len(row) != m for row in allocation + maximum):
        raise ValueError("Неверное количество ресурсов в строке")

    if any(
        maximum[i][j] < allocation[i][j]
        for i in range(n)
        for j in range(m)
    ):
        raise ValueError("Max не может быть меньше Allocation")

    need = [
        [
            maximum[i][j] - allocation[i][j]
            for j in range(m)
        ]
        for i in range(n)
    ]

    return available, allocation, maximum, need


def is_safe(available, allocation, need):
    work = available.copy()
    finished = [False] * len(allocation)
    sequence = []

    while len(sequence) < len(allocation):
        found = False

        for i in range(len(allocation)):
            if finished[i]:
                continue

            if all(
                need[i][j] <= work[j]
                for j in range(len(work))
            ):
                work = [
                    work[j] + allocation[i][j]
                    for j in range(len(work))
                ]

                finished[i] = True
                sequence.append(f"P{i}")
                found = True

        if not found:
            return False, []

    return True, sequence


def request_resources(available, allocation, need, pid, request):
    n = len(allocation)
    m = len(available)

    if not 0 <= pid < n:
        return False, "Неизвестный процесс"

    if len(request) != m or any(value < 0 for value in request):
        return False, "Некорректный вектор запроса"

    if any(request[j] > need[pid][j] for j in range(m)):
        return False, "Запрос превышает Need процесса"

    if any(request[j] > available[j] for j in range(m)):
        return False, "Недостаточно доступных ресурсов"

    # Временно выделяем ресурсы.
    for j in range(m):
        available[j] -= request[j]
        allocation[pid][j] += request[j]
        need[pid][j] -= request[j]

    safe, sequence = is_safe(available, allocation, need)

    if safe:
        return True, "Запрос разрешён. Безопасная последовательность: " + " -> ".join(sequence)

    # Откат: восстанавливаем исходное состояние.
    for j in range(m):
        available[j] += request[j]
        allocation[pid][j] -= request[j]
        need[pid][j] += request[j]

    return False, "Запрос отклонён: состояние небезопасно. Изменения отменены."


def main():
    if len(sys.argv) != 2:
        print(f"Использование: python3 {sys.argv[0]} bank1.txt")
        sys.exit(1)

    available, allocation, maximum, need = load_state(sys.argv[1])

    print("Available:", available)
    print("Need:")
    for i, row in enumerate(need):
        print(f"P{i}: {row}")

    safe, sequence = is_safe(available, allocation, need)

    if safe:
        print("SAFE")
        print("Безопасная последовательность:", " -> ".join(sequence))
    else:
        print("UNSAFE")
        print("Безопасная последовательность не найдена.")

    print()
    answer = input(
        "Проверить запрос ресурсов? (y/n): "
    ).strip().lower()

    if answer == "y":
        pid = int(input("Номер процесса (например, 1 для P1): "))
        request = list(map(
            int,
            input(f"Введите {len(available)} числа запроса через пробел: ").split()
        ))

        accepted, message = request_resources(
            available, allocation, need, pid, request
        )

        print(message)
        print("Available после проверки:", available)


if __name__ == "__main__":
    main()
