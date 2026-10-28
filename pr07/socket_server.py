import os
import signal
import socket
import multiprocessing
from fifo_server import calculate

SOCKET_PATH = "/tmp/pr07_server.sock"
server_socket = None


def handle_client(connection):
    with connection:
        file = connection.makefile("r", encoding="utf-8")
        expression = file.readline().strip()

        if not expression:
            return

        try:
            result = calculate(expression)
            response = f"OK|{result}\n"
        except Exception as error:
            response = f"ERROR|{error}\n"

        connection.sendall(response.encode("utf-8"))


def cleanup(*_):
    global server_socket

    if server_socket is not None:
        server_socket.close()

    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    raise SystemExit(0)


def main():
    global server_socket

    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server_socket = server
        server.bind(SOCKET_PATH)
        server.listen(10)

        print("Unix-сокет сервер запущен.")
        print(f"Сокет: {SOCKET_PATH}")
        print("Ожидание клиентов. Для остановки нажми Ctrl+C.")

        while True:
            connection, _ = server.accept()

            process = multiprocessing.Process(
                target=handle_client,
                args=(connection,),
            )
            process.start()
            connection.close()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
