#!/bin/sh
set -eu
cd "$(dirname "$0")"
if ! command -v gcc >/dev/null 2>&1; then
  echo 'Falta gcc en Milk-V: apt-get update && apt-get install gcc' >&2
  exit 2
fi
gcc -O2 -std=c11 -D_DEFAULT_SOURCE -Wall -Wextra spi_master.c -o spi_master
chmod +x spi_master
echo 'Compilado ./spi_master para la arquitectura de la Milk-V'
