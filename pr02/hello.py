#!/usr/bin/env python3

import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print(f"Использование: {sys.argv[0]} <файл>", file=sys.stderr)
        return 1

    file_path = Path(sys.argv[1])

    try:
        with file_path.open("rb") as file:
            content = file.read()
    except OSError as error:
        print(f"Ошибка чтения файла: {error}", file=sys.stderr)
        return 1

    print(f"Размер файла: {len(content)} байт")
    return 0


if __name__ == "__main__":
    sys.exit(main())
