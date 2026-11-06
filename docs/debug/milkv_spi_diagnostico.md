# Diagnóstico SPI — 5 de noviembre de 2026

**Actualizaci?n posterior:** Andrew autoriz? programar la versi?n corregida; se obtuvieron tres transferencias f?sicas v?lidas. Ver [validaci?n posterior](milkv_validacion_post_systick.md). Las restricciones de programaci?n y resultados de fallo siguientes describen la sesi?n anterior.

## Resultado y límites

**Causa de bloqueo identificada en la STM32 conectada:** SysTick permanece activo
en un handler de bucle infinito, con MISO configurado como salida en cero. Dos
transferencias C y una Python reprodujeron 264 bytes cero, rechazados por el parser.
La consola Milk-V se recuperó por VM y USB-UART; ver
[diagnóstico USB](milkv_usb_diagnostico.md). **SPI no está funcional.**

Se preparó y compiló un handler SysTick correcto en el proyecto local. No se
programó: el binario instalado es diferente de la base del repositorio y Andrew
confirmó que sus compañeros realizaron iteraciones cuyas fuentes no tiene.
Sustituirlo por el proyecto local cambiaría más que el handler. Se conserva una
copia íntegra de Flash fuera de Git.

Las respuestas históricas `53 43 02 F0 53 53 53 53` y `53 53 ...` fueron comunicadas
por Andrew, pero no se reprodujeron en esta sesión. No se explica su causa por
extrapolación de los ceros actuales.

## Versiones inspeccionadas

Base local: `81c0645`, continuación del ZIP integrado, ahora rama
`debug/milkv-usb-access`. Firmware local en `firmware/stm32/spi_polling/`;
maestro del ZIP en `backend/milkv_uart/milkv_stream.py`.

En la Milk-V se encontraron fuentes distintas en `/root/osciloscopio_final/milkv`:
`spi_master.c`, `spi_master.py`, `protocolo.py`, `preparar_gpio.sh`, `compilar.sh`,
`app.py` y `osciloscopio.service`. Se leyeron mediante `nl -ba` y `cat` sin editarlas.
El servicio existente estaba inactive; `app.py:26–30` elegiría el binario ejecutable
`spi_master` si existe, y solo en su ausencia el maestro Python. No existe fuente
STM32 en la búsqueda hasta profundidad 3 de ese directorio de proyecto.

SHA256 remoto, idéntico antes y después de las pruebas:

| Archivo | SHA256 |
|---|---|
| spi_master.c | d3be81aea3b21a8fe6c04162bcc7f99d21d369a96b99f8528f0d0601fc514e4d |
| spi_master.py | 84ccd70318f678f8dff02dbcc8c1862dac3cb85a22b2eead03df4a5975a06498 |
| protocolo.py | d4655e951af82ab4c9274bbd0cff028163af26c321958c065f7eb088afeabdc4 |
| spi_master, ejecutable | bf79e5688a3d02c4607ca54362e090189c9b1fcddf1265f83ea56394e93e171a |

`file spi_master`: ELF64 RISC-V, dinámico, ABI double-float; BuildID
`d9f61732eddd5c8b748bcd588b108c2f6cd1f75e`. No se demostró que ese ejecutable se
compilara de la fuente actual. Las fechas no sirven para esa comparación: el reloj
Milk-V marca agosto y el anfitrión noviembre.

## Cableado, GPIO y pinmux

| Señal | Milk-V Duo S J3 / GPIO | NUCLEO-L432KC | Lectura de Milk-V |
|---|---|---|---|
| MOSI | 19 / B13 / 461 | D11 / PB5 | out, 0, active_low=0 |
| MISO | 21 / B14 / 462 | D12 / PB4 | in, 0, active_low=0 |
| SCLK | 23 / B15 / 463 | D13 / PB3 | out, 0, active_low=0 |
| CS | 24 / B16 / 464 | A3 / PA4 | out, 1, active_low=0 |
| GND | 25 | GND | Continuidad no medida |

Correspondencia documental contrastada con [Milk-V Duo S](https://milkv.io/docs/duo/getting-started/duos)
y [ST UM1956, tabla 16](https://www.st.com/resource/en/user_manual/dm00231744.pdf).
J3 utiliza lógica de 3,3 V según Milk-V; no se midieron niveles con instrumento.
Lectura real `cvi_pinmux -r`: VIVO_D8/D7/D6/D5 seleccionan respectivamente
XGPIOB_13/14/15/16, registros 0300113C/140/144/148 con valor 3. gpiochip448 tiene
base 448, 32 líneas, etiqueta 3021000.gpio. No se ejecutó preparar_gpio.sh ni se
modificó el pinmux. No aparecieron procesos spi_master/app.py/milkv_stream activos.

En STM32, GPIOB_MODER=FFFFF13F: PB3 entrada, PB4 salida, PB5 entrada.
GPIOA_MODER=ABFFFCFF: PA4 entrada. GPIOB_IDR=0 y ODR=0; GPIOA_IDR=0000C010
incluye CS alto. Es consistente con el cableado previsto; no demuestra continuidad.
El firmware previo `firmware/stm32/src/main.c:30–34` usa PB3 como salida LED, pero
esa configuración no es la observada en la placa. No mezclar ambas inicializaciones.

## Maestros realmente instalados

- C `main():41–68`: valida preset 1/2/3, half_us 100–1000 (defecto de rigor:
  atoi/atol admiten sufijos no numéricos); abre 461/463/464 para salida y 462 para
  lectura. CS alto/SCLK bajo/MOSI bajo, 20 ms; CS bajo, 15 ms; envía preset en
  primer byte y ceros en el resto. Bit MSB-first; presenta MOSI, espera, sube CLK,
  espera, lee MISO, baja CLK, espera. Intención modo 0.
- C `get():30–34` hace lseek antes de read y rechaza read corto; un carácter distinto
  de '1' se interpreta como cero. `set():26–28` comprueba escrituras. `delay():36–38`
  reanuda nanosleep tras EINTR. Las salidas se restauran solo en la ruta normal;
  `die()` puede dejar CS bajo si falla durante una transferencia.
- Python `main():20–46`: mismo orden de señales, 264 bytes, pausas de 200 µs y
  preparación 20/15 ms. `r():16–18` reposiciona el descriptor, pero read vacío se
  convierte en False sin error. Usa finally para liberar CS/bajar CLK/MOSI, aunque
  una excepción en ese cleanup puede interrumpirlo. No aplica half_us configurable.
- Ninguno prepara pinmux/direcciones. `preparar_gpio.sh:4–7` configura mux y
  `:8–15` configura entrada MISO, salidas bajas MOSI/CLK y CS alto. El comentario
  de EXTI en C:50 no demuestra qué variante STM32 está cargada.
- `app.py:40–41` mata la adquisición si excede 3,4 s. Esto puede saltarse el cleanup
  de C o Python; riesgo pendiente, no la causa probada de los ceros actuales.

Se conservó bit-banging. `CONFIG_SPI` está deshabilitado en el kernel instalado;
no se usó spidev ni se propuso recuperarlo. Las pausas solicitan un mínimo ideal
1,2672 s por 264 B, antes de syscalls y planificación. Las mediciones de duración
abajo no son una medida de frecuencia uniforme ni de integridad eléctrica.

## Firmware local y protocolo

`firmware/stm32/spi_polling/src/main.c`:

- `gpio_spi_slave_init():87–109`: entradas PB3/PB5, salida push-pull PB4 inicialmente
  baja, PA4 entrada pull-up. PB4 sigue siendo salida con CS alto.
- `slave_transfer():251–279`: polling de niveles, índices locales reiniciados en
  cada llamada; prepara MISO en bajo y lee MOSI en alto. No EXTI ni SPI/DMA.
  `wait_clock():241–248` limita cada espera a 100 ms usando HAL_GetTick, pero las
  esperas CS de líneas 254/272/278 son ilimitadas. Si el nivel de reloj ya coincide,
  wait_clock no comprueba CS de nuevo.
- `prepare_frame():175–235` captura antes de ofrecer respuesta; no atiende SPI
  mientras adquiere. No hay READY/ACK. A 100 Sa/s son 640 ms nominales por ventana;
  los 15 ms del maestro no prueban que esté preparada.
- `read_adc():133–151` dispara y polls conversiones secuenciales PA0/PA1; TIM2 UIF
  se observa desde CPU. No se modificó adquisición ni se ensayaron sus presets.

Trama: 0–1 SC, 2 preset, 3 estado, 4–5 secuencia uint16 LE, 6–261 los 64 pares
CH1/CH2 uint16 LE, 262–263 CRC16 CCITT-FALSE LE sobre 0–261: **264 bytes**.
`protocolo.py:19–44` instalado verifica longitud, firma, CRC, preset, estado y RAW
≤4095. Coincide estructuralmente con put16/crc16/prepare_frame locales. No se impuso
268 B ni se cambió el protocolo. [Detalle](../protocol/frame_sc.md).

El firmware local escribe SC incluso si el ADC falla: datos ADC cero no justifican
una cabecera cero. F0 no es uno de sus estados 00/10–17. Los `53` repetidos tampoco
prueban avance de bytes: requieren captura completa, versión y trazas.

## Evidencia del bloqueo en el dispositivo

ST-LINK serie `0672FF373146363143221241`, VID/PID 0483:374B, versión V2J48M35.
OpenOCD detectó Cortex-M4, tensión objetivo ~3,24 V, DBGMCU_IDCODE=10016435
(familia L43x/L44x), Flash size=0100 (256 KiB). Identificación compatible con la
NUCLEO-L432KC declarada; el ID de familia no identifica por sí solo el encapsulado.
Se usó `reset_config none`, init, lecturas mdw/mdh y dump_image; **sin halt, reset,
resume, comandos de escritura de memoria de aplicación ni programación Flash**.

```text
SCB_VTOR       E000ED08 = 00000000
SYSCFG_MEMRMP  40010000 = 00000000
Vector activo  0000003C = 08002069
Vector Flash   0800003C = 08002069
SCB_ICSR       E000ED04 = 0400F80F   (repetido en varias lecturas)
Instrucción    08002068 = E7FE       (Thumb: b .)
GPIOB_MODER    48000400 = FFFFF13F
GPIOB_IDR      48000410 = 00000000
GPIOB_ODR      48000414 = 00000000
```

VECTACTIVE=15 significa SysTick. El bit Thumb del vector da dirección 08002068,
que contiene un salto a sí mismo. VTOR=0 y MEMRMP=0, junto con la lectura del
alias, confirman que se consultó la tabla activa. Interpretación del registro
según [ST PM0214, ICSR y excepciones](https://www.st.com/resource/en/programming_manual/pm0214-stm32-cortexm4-mcus-and-mpus-programming-manual-stmicroelectronics.pdf).
Este bloqueo impide que el bucle de aplicación atienda SPI; MISO queda bajo.
No descarta problemas adicionales después de reparar el arranque.

Respaldo por lectura de 262144 bytes:
`C:\dev\7mo\Linux\stm32-before-debug-20261105.bin`, fuera de Git.
SHA256 `7491f434e50da55a6961fafcf1eb428a2b8fe3f397f6064b8809fa318cde7977`.
No se incluyeron opciones de configuración/option bytes en ese respaldo.

## Pruebas efectivamente ejecutadas

| Prueba | Resultado |
|---|---|
| UART Windows, .NET/PySerial | Falló apertura COM11: error dispositivo inexistente |
| UART VM 115200/8N1 | Prompt root@duos y comandos Linux obtenidos |
| C físico, transferencia 1 | exit 0; 264 bytes, todos cero; 1,810 s / 1167 bit/s reportados |
| C físico, transferencia 2 consecutiva | exit 0; 264 bytes, todos cero; 1,793 s / 1178 bit/s reportados |
| Python físico | exit 0; 264 bytes, todos cero; tiempo total de subproceso 2,337 s |
| Parser instalado con esas tres respuestas | Rechaza cabecera: 00 00 00 00 00 00 00 00 |
| Parser instalado, trama sintética de 264 B | 64 pares, secuencia 1; CRC vector 123456789=29B1; PASS, no adquisición |
| 8 tests locales tests/milkv_uart/test_protocol_offline.py | PASS; GPIO/tiempos simulados, no ejecutan ARM |
| GCC Milk-V -fsyntax-only del maestro C | Sin errores; advertencia _DEFAULT_SOURCE redefinido por fuente y -D |
| Python compile() en memoria de maestro/protocolo | PY_SYNTAX_OK; -B, sin generar cachés |

Las tres pruebas físicas usaron subprocess.run con capture_output y timeout 8 s,
preset 2; C con half_us=200. No se redirigieron binarios crudos a la consola.
Se restauraron CS=1, CLK=0, MOSI=0 en finally. Servicio siguió inactive y niveles
finales se verificaron. No se midió ADC ni se probó patrón conocido: el firmware
está bloqueado y no se instaló otro para generar un patrón.

## Corrección mínima y compilación

Archivo añadido: `firmware/stm32/spi_polling/src/stm32l4xx_it.c`, handler
SysTick_Handler que llama a HAL_IncTick. No cambia main.c ni el firmware ADC+DMA.

Comandos locales desde la raíz del worktree:

```powershell
& C:\Users\justa\.platformio\penv\Scripts\python.exe -B tests/milkv_uart/test_protocol_offline.py
& C:\Users\justa\.platformio\penv\Scripts\platformio.exe run -d firmware/stm32/spi_polling -e nucleo_l432kc
& 'C:\Users\justa\.platformio\packages\toolchain-gccarmnoneeabi@1.70201.0\bin\arm-none-eabi-nm.exe' firmware/stm32/spi_polling/.pio/build/nucleo_l432kc/firmware.elf
```

Alcance build-validate: validación local limitada más diagnóstico físico controlado.
Build anterior: 6880 B Flash/496 B RAM; SysTick débil y Default_Handler en 08001BF8.
Build corregido: **SUCCESS, 6908 B Flash (+28), 496 B RAM**, sin advertencias
observadas. ststm32 19.5.0, CubeL4 1.18.1, GCC ARM 7.2.1. Primer intento de build
bloqueado por sandbox sobre platforms.lock; repetir con acceso autorizado a la
instalación existente funcionó. No se actualizaron dependencias.

`nm`: SysTick fuerte en 08001B68, Default_Handler en 08001C14 y HAL_IncTick en
0800023C. `objdump -d --start-address=0x08001b68 --stop-address=0x08001b70` muestra
`b.w 800023c <HAL_IncTick>`. La opción --disassemble=nombre no existe en este
objdump y se sustituyó por el rango de direcciones.
SHA256 binario local corregido:
`796baf9b6d3cd2fec27dc6605a6740ce28c13bfd21ab1393c552f6fbbffb651f`.

No se enlazó de nuevo el maestro C remoto ni se sustituyó su ejecutable. No se
escribieron fuentes o artefactos en la microSD, ni se cambiaron servicios/pinmux.
La compilación STM32 no demuestra funcionamiento físico de la corrección.

## Pendiente antes de declarar SPI funcional

Obtener las fuentes/ELF de la iteración instalada o acordar explícitamente la
versión a programar, manteniendo el respaldo. Aplicar solo el handler pertinente,
compilar, verificar objetivo y programar esa versión acordada. Después exigir
al menos dos transferencias consecutivas con SC, 264 bytes, CRC, estado y contenido
coherentes. Verificar secuencia y comparar C/Python. Solo entonces investigar
readiness/timeout/continuidad si persiste un fallo. No se requiere cambiar hardware,
reinstalar Debian ni habilitar SPI convencional de Milk-V.
