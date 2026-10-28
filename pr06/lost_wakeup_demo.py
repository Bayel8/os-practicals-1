import threading

condition = threading.Condition()
ready = False


def worker():
    global ready

    with condition:
        if not ready:
            print("Поток: ожидаю уведомление")
            condition.wait()

        if ready:
            print("Поток: условие выполнено")
        else:
            print("ОШИБКА: поток проснулся, но условие не выполнено")


thread = threading.Thread(target=worker)
thread.start()

with condition:
    while not condition._waiters:
        condition.wait(timeout=0.01)

    # Имитируем уведомление без выполнения условия.
    condition.notify_all()

thread.join()

print("Демонстрация завершена.")
