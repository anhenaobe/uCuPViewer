#!/bin/sh
set -eu
cd "$(dirname "$0")"
if [ "$#" -eq 1 ]; then
    PORT="$1"
else
    set -- /dev/ttyACM*
    if [ ! -e "$1" ]; then
        echo 'ERROR: No encuentro /dev/ttyACM*. La STM32 debe estar conectada por el USB ST-LINK.' >&2
        echo 'Prueba: ls /dev/ttyACM* /dev/serial/by-id/*' >&2
        exit 1
    fi
    if [ "$#" -ne 1 ]; then
        echo 'Hay varios /dev/ttyACM*. Especifica uno: ./iniciar.sh /dev/ttyACM0' >&2
        exit 1
    fi
    PORT="$1"
fi
exec python3 pc_dashboard_directo.py --serial "$PORT"
