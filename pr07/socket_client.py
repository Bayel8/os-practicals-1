import socket
import sys

SOCKET_PATH = "/tmp/pr07_server.sock"


def main():
    if len(sys.argv) < 2:
        print('Использование: python3 socket_client.py "10 + 5"')
        sys.exit(1)

    expression = " ".join(sys.argv[1:])

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(SOCKET_PATH)
            client.sendall((expression + "\n").encode("utf-8"))

            response = b""
            while not response.endswith(b"\n"):
                chunk = client.recv(4096)
                if not chunk:
                    break
                response += chunk

        status, result = response.decode("utf-8").strip().split("|", 1)

        if status == "OK":
            print(f"Выражение: {expression}")
            print(f"Результат: {result}")
        else:
            print(f"Ошибка вычисления: {result}")

    except (OSError, ValueError) as error:
        print(f"Ошибка клиента: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
