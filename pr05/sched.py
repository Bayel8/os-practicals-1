#!/usr/bin/env python3

import argparse
from collections import deque
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int


def pid_number(pid):
    """Возвращает числовую часть идентификатора, например P12 -> 12."""
    return int(pid[1:])


def load_processes(filename):
    """Читает процессы из файла, пропуская пустые строки и комментарии."""
    processes = []

    with open(filename, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split()

            if len(parts) != 4:
                raise ValueError(
                    f"{filename}:{line_number}: ожидалось 4 поля"
                )

            pid, arrival, burst, priority = parts

            process = Process(
                pid=pid,
                arrival=int(arrival),
                burst=int(burst),
                priority=int(priority),
            )

            if process.arrival < 0 or process.burst <= 0:
                raise ValueError(
                    f"{pid}: arrival должен быть >= 0, burst должен быть > 0"
                )

            if process.priority < 0:
                raise ValueError(f"{pid}: priority не может быть отрицательным")

            processes.append(process)

    if not processes:
        raise ValueError(f"В файле {filename} нет процессов")

    if len({p.pid for p in processes}) != len(processes):
        raise ValueError("PID процессов должны быть уникальными")

    return sorted(
        processes,
        key=lambda p: (p.arrival, pid_number(p.pid))
    )


def simulate(processes, algorithm, **params):
    """
    Возвращает интервалы (start, end, pid).

    Поддерживаемые алгоритмы:
    fcfs, sjf, srtf, priority, rr.

    RR: процессы, прибывшие в момент окончания кванта,
    добавляются в очередь раньше вытесненного процесса.
    """
    algorithm = algorithm.lower()

    allowed = {"fcfs", "sjf", "srtf", "priority", "rr"}
    if algorithm not in allowed:
        raise ValueError(f"Неизвестный алгоритм: {algorithm}")

    if algorithm == "rr":
        quantum = params.get("quantum", 3)
        if quantum <= 0:
            raise ValueError("Квант должен быть положительным")
    else:
        quantum = None

    jobs = sorted(
        processes,
        key=lambda p: (p.arrival, pid_number(p.pid))
    )

    remaining = {p.pid: p.burst for p in jobs}
    intervals = []
    time = 0
    index = 0
    ready = deque()

    def add_interval(start, end, pid):
        if start >= end:
            return

        if intervals and intervals[-1][2] == pid and intervals[-1][1] == start:
            old_start, _, old_pid = intervals[-1]
            intervals[-1] = (old_start, end, old_pid)
        else:
            intervals.append((start, end, pid))

    def admit_until(now):
        nonlocal index
        while index < len(jobs) and jobs[index].arrival <= now:
            ready.append(jobs[index])
            index += 1

    def choose_sjf():
        return min(
            ready,
            key=lambda p: (p.burst, p.arrival, pid_number(p.pid))
        )

    def choose_priority():
        return min(
            ready,
            key=lambda p: (p.priority, p.arrival, pid_number(p.pid))
        )

    def choose_srtf():
        return min(
            ready,
            key=lambda p: (
                remaining[p.pid],
                p.arrival,
                pid_number(p.pid)
            )
        )

    if algorithm in {"fcfs", "sjf"}:
        while index < len(jobs) or ready:
            admit_until(time)

            if not ready:
                time = jobs[index].arrival
                admit_until(time)

            if algorithm == "fcfs":
                current = ready.popleft()
            else:
                current = choose_sjf()
                ready.remove(current)

            start = time
            time += remaining[current.pid]
            remaining[current.pid] = 0
            add_interval(start, time, current.pid)

    elif algorithm in {"srtf", "priority"}:
        completed = 0
        total = len(jobs)

        while completed < total:
            admit_until(time)

            if not ready:
                if index < len(jobs):
                    time = jobs[index].arrival
                    admit_until(time)
                else:
                    break

            current = (
                choose_srtf()
                if algorithm == "srtf"
                else choose_priority()
            )

            ready.remove(current)

            start = time
            time += 1
            remaining[current.pid] -= 1
            add_interval(start, time, current.pid)

            if remaining[current.pid] == 0:
                completed += 1
            else:
                ready.append(current)

    else:  # Round Robin
        completed = 0
        total = len(jobs)

        while completed < total:
            admit_until(time)

            if not ready:
                if index < len(jobs):
                    time = jobs[index].arrival
                    admit_until(time)
                else:
                    break

            current = ready.popleft()
            run_time = min(quantum, remaining[current.pid])

            start = time
            end = time + run_time

            # Сначала выполняем квант.
            remaining[current.pid] -= run_time
            time = end
            add_interval(start, end, current.pid)

            # Затем добавляем процессы, прибывшие до конца кванта,
            # и только после этого возвращаем вытесненный процесс.
            admit_until(time)

            if remaining[current.pid] > 0:
                ready.append(current)
            else:
                completed += 1

    return intervals


def calculate_metrics(processes, intervals):
    """Вычисляет ожидание, оборот, отклик и загрузку CPU."""
    first_start = {}
    completion = {}
    executed = {p.pid: 0 for p in processes}

    for start, end, pid in intervals:
        first_start.setdefault(pid, start)
        completion[pid] = end
        executed[pid] += end - start

    total_time = max((end for _, end, _ in intervals), default=0)
    busy_time = sum(end - start for start, end, _ in intervals)

    waiting = []
    turnaround = []
    response = []

    for p in processes:
        if p.pid not in completion:
            raise RuntimeError(f"Процесс {p.pid} не завершился")

        turn = completion[p.pid] - p.arrival
        wait = turn - p.burst
        resp = first_start[p.pid] - p.arrival

        waiting.append(wait)
        turnaround.append(turn)
        response.append(resp)

    return {
        "waiting": sum(waiting) / len(waiting),
        "turnaround": sum(turnaround) / len(turnaround),
        "response": sum(response) / len(response),
        "cpu_utilization": (
            100 * busy_time / total_time if total_time else 0.0
        ),
        "switches": max(0, len(intervals) - 1),
        "busy_time": busy_time,
        "total_time": total_time,
    }


def print_gantt(intervals):
    print("\nДиаграмма Ганта:")
    if not intervals:
        print("(нет интервалов)")
        return

    print(" -> ".join(
        f"{pid}[{start}-{end}]"
        for start, end, pid in intervals
    ))


def main():
    parser = argparse.ArgumentParser(
        description="Симулятор алгоритмов планирования CPU"
    )
    parser.add_argument(
        "--algo",
        choices=["fcfs", "sjf", "srtf", "priority", "rr"],
        required=True,
    )
    parser.add_argument("--quantum", type=int, default=3)
    parser.add_argument("file", help="Входной файл процессов")

    args = parser.parse_args()

    processes = load_processes(args.file)

    params = {}
    if args.algo == "rr":
        params["quantum"] = args.quantum

    intervals = simulate(processes, args.algo, **params)
    metrics = calculate_metrics(processes, intervals)

    print(f"Алгоритм: {args.algo.upper()}")
    print(f"Файл: {args.file}")
    print(f"Количество процессов: {len(processes)}")

    print_gantt(intervals)

    print("\nМетрики:")
    print(f"Среднее ожидание: {metrics['waiting']:.2f}")
    print(f"Средний оборот: {metrics['turnaround']:.2f}")
    print(f"Среднее время отклика: {metrics['response']:.2f}")
    print(f"Загрузка CPU: {metrics['cpu_utilization']:.2f}%")
    print(f"Число переключений: {metrics['switches']}")
    print(f"Занято CPU: {metrics['busy_time']}")
    print(f"Общее время симуляции: {metrics['total_time']}")


if __name__ == "__main__":
    main()
