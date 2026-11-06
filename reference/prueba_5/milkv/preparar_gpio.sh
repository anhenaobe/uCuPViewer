#!/bin/sh
set -eu
# GPIOB_13 ..16 (chip448, nombres y números comprobados previamente).
cvi_pinmux -w VIVO_D8/XGPIOB_13
cvi_pinmux -w VIVO_D7/XGPIOB_14
cvi_pinmux -w VIVO_D6/XGPIOB_15
cvi_pinmux -w VIVO_D5/XGPIOB_16
for n in 461 462 463 464; do
    [ -d "/sys/class/gpio/gpio$n" ] || echo "$n" > /sys/class/gpio/export
    echo in > "/sys/class/gpio/gpio$n/direction"
done
echo low > /sys/class/gpio/gpio461/direction # MOSI
echo low > /sys/class/gpio/gpio463/direction # SCLK
echo high > /sys/class/gpio/gpio464/direction # CS
echo "SPI GPIO configurado: MOSI=461 MISO=462 SCK=463 CS=464"
