# Auditoría técnica del prototipo SPI polling

Fecha: 2026-11-05. Base revisada origin/main 10ec48f. Inspección y compilación offline;
ninguna conexión UART/GPIO, programación ni prueba física realizada en esta tarea.
Revisión independiente de evidencia y corrección coinciden en los hallazgos siguientes.

## Inventario y alcance
Raíz P = reference/prototipos/spi_polling_zip/osc_spi_uart_pc/.
Cinco archivos originales: README.md, stm32/src/main.c, pc/milkv_stream.py,
pc/pc_dashboard_uart.py y pc/dashboard.html. No hay pruebas fuente originales.
Dos cachés .pyc excluidas. Faltan preparar_gpio.sh y platformio.ini de Prueba_SPI.
Autor/licencia desconocidos; no atribuir a integrantes. Ver README de procedencia.

## Hallazgos prioritarios
1. **Bloqueo de arranque reproducible por enlace en configuración aislada.**
   P/stm32/src/main.c:285 llama HAL_Init sin definir SysTick_Handler. El startup
   instalado STM32L432 weak-alias lo enlaza al Default_Handler. nm del ELF obtenido:
   08001bf8 T Default_Handler; 08001bf8 W SysTick_Handler. La primera interrupción
   SysTick entra al manejador por defecto; los timeouts HAL tampoco progresan como
   se espera. firmware/stm32/src/main.c:8 sí provee HAL_IncTick. El proyecto externo
   Prueba_SPI podría tener otro archivo ISR: pedir su ELF/fuentes antes de atribuir
   a esto la avería observada. No hay prueba física de causalidad.
2. **Timeout incompleto y CS bloqueante.** P/stm32/src/main.c:241–278, wait_clock y
   slave_transfer: timeout de flanco de 100 ms lleva a abort, pero abort y final
   esperan CS alto sin límite. CS atascado bajo congela el avance. Espera inicial
   de CS bajo también monopoliza CPU e impide otras tareas/heartbeat.
3. **Sin garantía de TX listo.** prepare_frame:178–235 captura antes de servir SPI;
   main:289–299 lo hace al arrancar y tras CS alto. capture de milkv_stream:43–67
   espera 20 ms antes y 15 ms después de CS bajo, sin READY. A 100 Sa/s la captura
   necesita nominalmente 640 ms. El bucle de Milk-V:113–124 mide sus 4 s desde inicio
   de transferencia: si esta tarda >=4 s no queda pausa entre ciclos. En arranque,
   reinicio o transferencia lenta pueden comenzar clocks antes de preparar respuesta.
4. **Firmware cargado importa.** El firmware principal ADC+DMA no implementa SPI y
   configura PB3 como salida LED (firmware/stm32/src/main.c:32–43). El ZIP requiere
   PB3 entrada SCLK. Si se conserva ese firmware y se conecta el reloj GPIO habrá
   dos salidas en la misma señal; no es incompatibilidad inevitable entre chips.
   El main del ZIP sí configura PB3 como entrada. Verificar versión antes de cablear.
5. **Requisitos ausentes.** README original:14–17 depende de configuración externa.
   milkv_stream:13,99–101 presupone GPIO461–464 exportados y configurados. No es
   posible verificar numeración, pinmux ni dirección física desde el ZIP solo.

## Arquitectura y SPI software
PC ejecuta pc_dashboard_uart.SerialPort.install_remote: transfiere código Python
por consola UART de root a Milk-V; milkv_stream.main controla GPIO y devuelve líneas
SCOPE_DATA JSON; PC sirve HTTP. No usa Ethernet. HTTP no reside en SBC (README original).
No ejecutar el cargador como prueba offline: envía órdenes reales por UART.

| Señal | Milk-V declarada / sysfs | STM32 |
|---|---|---|
| MOSI | B13 / 461 | PB5 entrada |
| MISO | B14 / 462 | PB4 salida push-pull |
| SCLK | B15 / 463 | PB3 entrada |
| CS | B16 / 464 | PA4 entrada pull-up |
| Referencia | GND | GND |

Fuente: README original:15; milkv_stream:13–23; main.c:29–38,86–110.
Milk-V es controlador; STM32 periférico. capture establece SCLK bajo, MOSI antes
flanco ascendente, lee MISO durante alto y vuelve bajo. slave_transfer presenta
MISO durante bajo y captura MOSI durante alto: intención modo0, MSB-first, CS bajo.
wait_clock observa niveles por polling, no hardware que capture flancos; puede
perder pulsos si se desprograma o interrumpe. MISO no se pone alta impedancia al
liberar CS: no es seguro compartir ese bus con otro periférico sin adaptación.
Tres sleeps de 200 us por bit en Python: mínimo solicitado de 600 us/bit,
~1667 bit/s y 1.2672 s por 264 bytes, sin syscalls, setup ni scheduler. No 1 MHz.
Pausas Linux superiores a100 ms disparan timeout periférico; subir frecuencia
reduce margen del polling. Son riesgos deducidos, no mediciones.

## Trama SC y comparación exacta
SC son los bytes ASCII 0x53,0x43, usados como firma (no nombre de comando).
Fuente: main.c:14–20, put16, crc16, prepare_frame; milkv_stream.capture:68–92.

| Campo | ZIP | Contrato v0.2 B1 | Compatibilidad / acción futura |
|---|---|---|---|
| Total |264 B|268 B|Incompatible; serializador nuevo aprobado|
| Cabecera |6 B|8 B|Reordenar/codificar campos|
| Firma |[0..1] SC|[0] 0x5A|Cambiar validación|
| Estado |[3], errores0x10..0x17|[1],0 OK; otros pendientes|Acordar mapa, no asumir equivalencia|
| Preset |[2],1/2/3|[3],0/1/2;3 experimental|Remapear explícitamente; no habilitar40k|
| Secuencia |[4..5] uint16 LE, contador ventana|[2], byte seq asociado solicitud|Rediseñar identidad/reintentos|
| N |implícito64|[4..5] uint16 LE64|Validar N explícito|
| Longitud payload |implícita256|[6..7] uint16 LE256|Añadir y validar|
| Payload |[6..261],64 pares uint16 LE|[8..263],mismo orden|Formato de muestras reutilizable|
| CRC |[262..263],sobre0..261|[264..265],sobre0..263|Mismo algoritmo, distinto rango|
| Padding |ninguno|[266..267]=0|Añadir2 B|
| Comando |primer byte MOSI preset; resto ceros|CMD8 B A5/opcode/arg/seq/reserva/CRC|Incompatible, nueva lógica|
| Respuesta |ventana previa full-duplex|ACK8 B separado antes de READ_WINDOW|Implementar estados después de aprobar|

264=6+256+2; 268=8+256+2+2. Diferencia4 B: +2 cabecera y +2 padding,
NO un CRC extra. CRC16 CCITT-FALSE initFFFF/polinomio1021, sin reflexión y almacenado
LE coincide en algoritmo. Comando del ZIP no tiene CRC ni ACK. Preset recibido se
aplica a la siguiente captura, no a la que se transmite. Contador no vincula pedido.
CS delimita 264 bytes. No hay resincronización por búsqueda de SC dentro del flujo.
Milk-V valida firma, CRC, preset conocido, estado y RAW<=4095; no comprueba continuidad
de secuencia. Trama con error válida en CRC se rechaza y no se grafica como correcta.

## ADC y bloqueos
main.c adc_init_safe:113–137 configura12 bits, PA0/IN5 y PA1/IN6, una conversión por
vez sin DMA y software start. prepare_frame configura TIM2 PSC15 y ARR periodo_us-1
para HSI16 y polls UIF antes de llamar read_adc dos veces. read_adc:140–159 configura
canal, inicia, espera hasta5 ms y detiene. No es TIM TRGO→ADC→DMA: jitter de CPU y
latencia HAL afectan instantes. Ventana64 pares intercalados LE en tx_frame; flags de
periodo perdido producen0x17, timeout timer0x16; otros errores0x10..0x15 distinguen
init/calibración/timer/config/start/conversión. Dependen de tick válido.
La misma CPU captura o transmite, sin concurrencia ni doble buffer. Memset limpia
trama y CRC incluye el estado; captura parcial puede enviarse marcada error. No se
observan offsets de escritura fuera de264 B en put16 con estos índices. Esto no
constituye prueba de memoria en placa. El buffer estable durante transmisión es
una propiedad útil; la exclusión bloqueante no debe trasladarse al driver definitivo.

## Verificaciones realizadas y límites
- Python estándar: python -B docs/reviews/tests/test_protocol_offline.py:4 PASS.
  Vector CRC123456789→29B1, trama sintética64 pares, rechazo corrupción y cabecera.
  w/r/sleep sustituidos: ningún GPIO real. No simula scheduler ni esclavo físico.
- Copia aislada del main.c sin cambios en C:/dev/7mo/Linux/milk-build-probe;
  platformio.ini tomado de firmware/stm32, no aportado por el ZIP.
  pio run -d C:/dev/7mo/Linux/milk-build-probe -e nucleo_l432kc:SUCCESS;
  6880 B Flash,496 B RAM estática; Core6.2.0,ststm32 19.5.0,CubeL4 1.18.1,GCC7.2.1.
  nm confirmó alias SysTick/Default_Handler. Sin upload, debug ni prueba física.
- Inspección de fuentes: no evidencia de credenciales embebidas; sesión root requerida
  no equivale a credencial incluida. Autoría/licencia y pinmux externo sin resolver.
- Fuentes importadas comparadas por SHA256 con entradas ZIP; ZIP original intacto.
- Firmware, profesor, backend, frontend, infraestructura y contrato fuera del diff.

No puede confirmarse el fallo físico original sin conocer el firmware realmente
cargado, ISR externas, pinmux, cableado y trazas. Una futura prueba física requiere
permiso explícito y confirmar conexión. No se implementa ninguna corrección aquí.
