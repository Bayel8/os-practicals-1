from pathlib import Path

COUNT = 10_000_000
OUTPUT = Path(__file__).parent / "numbers.txt"


def main():
    with OUTPUT.open("w", encoding="utf-8") as file:
        for number in range(1, COUNT + 1):
            file.write(f"{number}\n")

    print(f"Файл создан: {OUTPUT}")
    print(f"Количество чисел: {COUNT}")
    print(f"Ожидаемая сумма: {COUNT * (COUNT + 1) // 2}")


if __name__ == "__main__":
    main()
