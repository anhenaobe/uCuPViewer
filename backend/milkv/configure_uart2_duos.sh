#!/bin/sh
# Ejecutar COMO ROOT en Milk-V Duo S cuando se haya confirmado el device tree y UART2.
# Nunca usa el duo-pinmux antiguo que lista GP0..GP27 (variante equivocada).
set -eu
MODEL=$(tr -d '\000' </proc/device-tree/model)
case "$MODEL" in *'DuoS'*|*'Duo S'*) ;; *) echo "ERROR: modelo $MODEL no es Duo S" >&2; exit 1;; esac
if ! command -v duos-pinmux >/dev/null 2>&1; then
    echo 'Falta duos-pinmux (específico de Duo S). Consulta README.' >&2; exit 1
fi
if ! duos-pinmux -p | grep -qx B11 || ! duos-pinmux -p | grep -qx B12; then
    echo 'ERROR: el binario duos-pinmux no corresponde al pinout Duo S' >&2; exit 1
fi
if grep '^2:' /proc/tty/driver/serial | grep -q 'uart:unknown'; then
    echo 'ALTO: ttyS2 NO fue inicializado por kernel/device tree.' >&2
    echo 'Habilita UART2 en el DT apropiado de tu Debian antes de tocar el pinmux.' >&2
    exit 2
fi
echo 'Configurando J3 pin 11 B11=TX2; pin 13 B12=RX2'
duos-pinmux -w B11/UART2_TX
duos-pinmux -w B12/UART2_RX
duos-pinmux -r B11
duos-pinmux -r B12
stty -F /dev/ttyS2 115200 raw -echo -crtscts
printf '\nUART2 listo para una PRUEBA de loopback TX-RX en J3.\n'
