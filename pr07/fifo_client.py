import os
import sys
import uuid

REQUEST_FIFO = "/tmp/pr07_requests.fifo"
RESPONSE_FIFO = "/tmp/pr07_responses.fifo"


def main():
    if len(sys.argv) < 2:
        print('Использование: python3 fifo_client.py "10 + 5"')
        sys.exit(1)

    expression = " ".join(sys.argv[1:])
    client_id = uuid.uuid4().hex

    if not os.path.exists(REQUEST_FIFO) or not os.path.exists(RESPONSE_FIFO):
        print("Ошибка: FIFO не найдены. Сначала запусти сервер.")
        sys.exit(1)

    # Сначала отправляем запрос, затем открываем канал ответа.
    with open(REQUEST_FIFO, "w", encoding="utf-8") as requests:
        requests.write(f"{client_id}|{expression}\n")
        requests.flush()

    with open(RESPONSE_FIFO, "r", encoding="utf-8") as responses:
        for line in responses:
            parts = line.rstrip("\n").split("|", 2)

            if len(parts) == 3 and parts[0] == client_id:
                _, status, result = parts

                if status == "OK":
                    print(f"Выражение: {expression}")
                    print(f"Результат: {result}")
                else:
                    print(f"Ошибка вычисления: {result}")

                return

    print("Сервер закрыл канал без ответа.")
    sys.exit(1)


if __name__ == "__main__":
    main()
