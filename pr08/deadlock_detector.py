#!/usr/bin/env python3

import json
import sys
from collections import defaultdict


def build_wait_for_graph(events):
    owners = {}
    waiting = {}
    processes = set()

    for number, event in enumerate(events, start=1):
        action = event.get("event")
        pid = event.get("pid")
        resource = event.get("resource")

        if action not in {"acquire", "wait", "release"}:
            raise ValueError(f"Событие {number}: неизвестный тип {action!r}")

        if not isinstance(pid, str) or not pid:
            raise ValueError(f"Событие {number}: неверный pid")

        if not isinstance(resource, str) or not resource:
            raise ValueError(f"Событие {number}: неверный resource")

        processes.add(pid)

        if action == "acquire":
            current_owner = owners.get(resource)

            if current_owner is None:
                owners[resource] = pid
                waiting.pop(pid, None)
            elif current_owner == pid:
                raise ValueError(
                    f"Событие {number}: повторный захват {resource} процессом {pid}"
                )
            else:
                waiting[pid] = resource

        elif action == "wait":
            waiting[pid] = resource

        elif action == "release":
            if owners.get(resource) != pid:
                raise ValueError(
                    f"Событие {number}: {pid} не владеет ресурсом {resource}"
                )

            del owners[resource]

    graph = defaultdict(set)

    for pid in processes:
        graph[pid]

    for pid, resource in waiting.items():
        owner = owners.get(resource)

        if owner is not None and owner != pid:
            graph[pid].add(owner)

    return graph


def find_cycle(graph):
    state = {node: 0 for node in graph}
    path = []

    def dfs(node):
        state[node] = 1
        path.append(node)

        for neighbor in sorted(graph[node]):
            if state[neighbor] == 0:
                cycle = dfs(neighbor)
                if cycle:
                    return cycle
            elif state[neighbor] == 1:
                start = path.index(neighbor)
                return path[start:] + [neighbor]

        path.pop()
        state[node] = 2
        return None

    for node in sorted(graph):
        if state[node] == 0:
            cycle = dfs(node)
            if cycle:
                return cycle

    return None


def main():
    if len(sys.argv) != 2:
        print(f"Использование: python3 {sys.argv[0]} events.json")
        sys.exit(1)

    try:
        with open(sys.argv[1], "r", encoding="utf-8") as file:
            events = json.load(file)

        if not isinstance(events, list):
            raise ValueError("Журнал должен содержать JSON-массив событий")

        graph = build_wait_for_graph(events)

        print("Граф ожидания:")
        for pid in sorted(graph):
            neighbors = sorted(graph[pid])
            print(f"{pid} -> {', '.join(neighbors) if neighbors else 'нет'}")

        cycle = find_cycle(graph)

        if cycle:
            print("DEADLOCK DETECTED")
            print("Цикл:", " -> ".join(cycle))
            print("Участники:", ", ".join(cycle[:-1]))
        else:
            print("DEADLOCK NOT DETECTED")

    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Ошибка: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
