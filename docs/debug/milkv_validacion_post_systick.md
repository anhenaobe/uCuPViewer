# Validación física después de corregir SysTick

Sesión posterior al diagnóstico del 5 de noviembre de 2026. Andrew autorizó
explícitamente reemplazar el firmware instalado por la versión corregida del
repositorio, conservando el respaldo. Esta evidencia actualiza el estado pendiente
de programación de los documentos de diagnóstico anteriores.

## Programación

Se reidentificó ST-LINK `0672FF373146363143221241`, Cortex-M4, IDCODE `10016435`,
Flash de 256 KiB y tensión aproximada 3,246 V. Se comprobó el SHA256 del respaldo
original `7491f434e50da55a6961fafcf1eb428a2b8fe3f397f6064b8809fa318cde7977` y del
binario corregido `796baf9b6d3cd2fec27dc6605a6740ce28c13bfd21ab1393c552f6fbbffb651f`.
El respaldo sigue en `C:\dev\7mo\Linux\stm32-before-debug-20261105.bin`.

OpenOCD, con la serie indicada y target/stm32l4x.cfg, ejecutó:

```text
program firmware/stm32/spi_polling/.pio/build/nucleo_l432kc/firmware.elf verify reset exit
```

Resultado: Programming Finished, **Verified OK**, Resetting Target. Se reinició
solo STM32; Milk-V no se reinició. OpenOCD extendió el borrado hasta el límite de
página 08001FFF, comportamiento reportado durante la programación. No se cambiaron
option bytes. La imagen programada procede del commit 54a8396 y conserva el
firmware polling del repositorio con el handler SysTick añadido.

Lectura posterior sin halt/reset: vector activo en 0000003C = **08001B69**;
ICSR = **00000000**, sin excepción activa en ese instante. Ya no apunta al bucle
infinito 08002068 de la versión anterior.

## Transferencias reales

Acceso Windows → SSH localhost a vmmm → Prolific ttyUSB0 → root@duos. Antes de
probar: servicio osciloscopio inactive, sin otro maestro detectado; direcciones
461 out, 462 in, 463 out, 464 out; reposo MOSI=0/SCLK=0/CS=1.

Desde `/root/osciloscopio_final/milkv`, sin modificar sus archivos, se ejecutaron
secuencialmente estos subprocesos, capturando stdout en RAM, timeout 8 s y pausa
de 1 s entre transferencias. El parser instalado `protocolo.decode` verificó cada
respuesta. Finalmente se restauraron CS=1, SCLK=0 y MOSI=0.

| Comando | Longitud | Cabecera hexadecimal | Secuencia | Resultado |
|---|---|---|---|---|
| ./spi_master 2 200 | 264 | 53 43 02 00 01 00 FF 0F | 1 | CRC/estado/rango válidos, 64 pares |
| ./spi_master 2 200 | 264 | 53 43 02 00 02 00 F0 0F | 2 | CRC/estado/rango válidos, 64 pares |
| python3 -B spi_master.py 2 | 264 | 53 43 02 00 03 00 FF 0F | 3 | CRC/estado/rango válidos, 64 pares |

Todos terminaron con exit 0. C reportó 1,783 s/1185 bit/s y 1,791 s/1179 bit/s;
son velocidades efectivas incluyendo esperas, no frecuencia uniforme medida de SCLK.

Primer/último par RAW de cada ventana:

- Secuencia 1: (4095, 0) / (4088, 0).
- Secuencia 2: (4080, 0) / (4080, 0).
- Secuencia 3: (4095, 0) / (4095, 0).

**El enlace SPI funciona en estas tres transferencias**, con SC, longitud, CRC,
estado y secuencia coherentes. Desapareció el fallo reproducido de 264 bytes cero.
No hubo error de protocolo en estas pruebas. No es un ensayo de estabilidad
prolongada ni demuestra ausencia de todos los fallos de sincronización posibles.

CH1 próximo a escala completa y CH2 cero no equivalen a tensiones verificadas:
no se midieron las entradas ni se conectó un generador. La tasa nominal es preset
2 (1000 Sa/s/canal); no se verificó experimentalmente su precisión ni los otros
presets. Los tiempos de muestras calculados por el parser no son mediciones.

## Alcance y estado final

Se sustituyó el firmware STM32 con autorización; no se modificó ADC, protocolo,
maestros Milk-V, dashboard, pinmux, kernel ni servicios durante esta continuación.
La sustitución utiliza la versión del repositorio y no pretende conservar cambios
de fuentes desconocidas de la imagen anterior; esa imagen está respaldada.

Se cerraron los sondeos UART y la sesión SSH y se retiró la redirección temporal.
La VM permanece encendida con el Prolific asignado. No se inició osciloscopio.service.
Siguiente trabajo separado: caracterizar entradas/tasas y estabilidad de muchas
ventanas, sin confundir esta recuperación SPI con validación completa del osciloscopio.
