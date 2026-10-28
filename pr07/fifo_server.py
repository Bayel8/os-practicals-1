import stat
import ast
import operator
import os
import signal

REQUEST_FIFO = "/tmp/pr07_requests.fifo"
RESPONSE_FIFO = "/tmp/pr07_responses.fifo"

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def calculate(expression):
    """Вычисляет арифметическое выражение без eval()."""
    if len(expression) > 200:
        raise ValueError("Выражение слишком длинное")

    def evaluate(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Слишком большая степень")

            result = OPERATORS[type(node.op)](left, right)

            if isinstance(result, (int, float)) and abs(result) > 1e100:
                raise ValueError("Результат слишком большой")

            return result

        if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
            return OPERATORS[type(node.op)](evaluate(node.operand))

        raise ValueError("Недопустимое выражение")

    tree = ast.parse(expression, mode="eval")
    return evaluate(tree.body)


def cleanup(*_):
    for path in (REQUEST_FIFO, RESPONSE_FIFO):
        if os.path.exists(path):
            os.unlink(path)
    raise SystemExit(0)


def main():
    for path in (REQUEST_FIFO, RESPONSE_FIFO):
        if os.path.exists(path):
            if not stat.S_ISFIFO(os.stat(path).st_mode):
                raise RuntimeError(f"Путь существует и не является FIFO: {path}")
            os.unlink(path)
        os.mkfifo(path)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    print("FIFO-сервер запущен.")
    print(f"Запросы: {REQUEST_FIFO}")
    print(f"Ответы:  {RESPONSE_FIFO}")
    print("Для остановки нажми Ctrl+C.")

    while True:
        with open(REQUEST_FIFO, "r", encoding="utf-8") as requests:
            for line in requests:
                line = line.strip()
                if not line:
                    continue

                try:
                    client_id, expression = line.split("|", 1)

                    if expression.strip().lower() == "exit":
                        result = "Сервер продолжает работу"
                    else:
                        result = str(calculate(expression))

                    response = f"{client_id}|OK|{result}\n"

                except Exception as error:
                    client_id = line.split("|", 1)[0]
                    response = f"{client_id}|ERROR|{error}\n"

                with open(RESPONSE_FIFO, "w", encoding="utf-8") as replies:
                    replies.write(response)
                    replies.flush()


if __name__ == "__main__":
    main()
