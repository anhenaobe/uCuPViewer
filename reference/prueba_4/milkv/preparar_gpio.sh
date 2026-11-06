#!/bin/sh
set -eu
cvi_pinmux -w VIVO_D8/XGPIOB_13
cvi_pinmux -w VIVO_D7/XGPIOB_14
cvi_pinmux -w VIVO_D6/XGPIOB_15
cvi_pinmux -w VIVO_D5/XGPIOB_16
for n in 461 462 463 464; do
    if [ ! -d "/sys/class/gpio/gpio$n" ]; then
        echo "$n" > /sys/class/gpio/export
    fi
    echo in > /sys/class/gpio/gpio$n/direction
done
echo low  > /sys/class/gpio/gpio461/direction
echo low  > /sys/class/gpio/gpio463/direction
echo high > /sys/class/gpio/gpio464/direction
echo 'GPIO listos: 461 MOSI, 462 MISO, 463 SCLK, 464 CS'
