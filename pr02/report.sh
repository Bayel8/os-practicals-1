#!/usr/bin/env bash

set -u

usage() {
    echo "Использование: $0 <каталог> <ERROR|WARN> [--top N]"
}

if [[ $# -lt 2 ]]; then
    usage >&2
    exit 1
fi

directory=$1
level=$2
top=""

if [[ ! -d "$directory" ]]; then
    echo "Ошибка: каталог '$directory' не существует." >&2
    exit 1
fi

if [[ "$level" != "ERROR" && "$level" != "WARN" ]]; then
    echo "Ошибка: уровень должен быть ERROR или WARN." >&2
    usage >&2
    exit 1
fi

if [[ $# -gt 2 ]]; then
    if [[ $# -ne 4 || "$3" != "--top" || ! "$4" =~ ^[1-9][0-9]*$ ]]; then
        echo "Ошибка: используйте --top N, где N — положительное целое число." >&2
        usage >&2
        exit 1
    fi
    top=$4
fi

result=$(
    find "$directory" -maxdepth 1 -type f -name '*.log' -print0 |
        xargs -0 -r grep -hE \
        "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2} ${level} module=[^[:space:]]+" |
        awk '{
            for (i = 1; i <= NF; i++) {
                if ($i ~ /^module=/) {
                    module = $i
                    sub(/^module=/, "", module)
                    count[module]++
                    break
                }
            }
        }
        END {
            for (module in count) {
                printf "%s %d\n", module, count[module]
            }
        }' |
        sort -k2,2nr -k1,1
)

printf 'Модуль | Количество записей (%s)\n' "$level"

if [[ -n "$result" ]]; then
    if [[ -n "$top" ]]; then
        printf '%s\n' "$result" | head -n "$top"
    else
        printf '%s\n' "$result"
    fi
fi
