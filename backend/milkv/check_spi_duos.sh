#!/bin/sh
# Diagnóstico SIN CAMBIAR el Device Tree, pinmux ni la configuración Linux.
set -u
echo "Modelo:"
tr '\000' '\n' < /proc/device-tree/model
echo "Nodos spidev expuestos por Linux:"
ls -l /dev/spidev* 2>/dev/null || echo "SIN /dev/spidev*: SPI no habilitado/expuesto al espacio de usuario"
echo "Controladores y mensajes de arranque SPI:"
dmesg 2>/dev/null | grep -Ei 'spi|spidev' | tail -25 || true
echo "Python spidev:"
python3 -c 'import spidev; print("python3-spidev OK")' 2>&1 || true
echo "Pinout propuesto Duo S (J3 3.3V): B13/19 MOSI(SDO), B14/21 MISO(SDI), B15/23 SCK, B16/24 CS, GND/20."
echo "NO conectar STM32 ni flashear DTB hasta validar pinmux y spidev reales."
