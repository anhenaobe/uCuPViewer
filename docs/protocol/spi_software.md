# SPI por software del desarrollo actual

Milk-V es controlador GPIO; STM32L432KC es periférico GPIO. Se mantiene este diseño:
la interfaz SPI convencional del montaje Milk-V está bloqueada/no disponible según
Andrew. La causa técnica aún no está documentada; no se propone spidev ni Device Tree.

## Señales identificadas, pendientes de verificación física
| Señal | Milk-V declarada | sysfs | STM32 |
|---|---|---|---|
|MOSI|B13|461|PB5 entrada|
|MISO|B14|462|PB4 salida push-pull|
|SCLK|B15|463|PB3 entrada|
|CS|B16|464|PA4 entrada pull-up|
|GND|tierra común|—|GND|
Fuentes: backend/milkv_uart/milkv_stream.py:13–23 y firmware/stm32/spi_polling/src/main.c:
29–38, gpio_spi_slave_init. Son números declarados, no pinout definitivo aprobado.
preparar_gpio.sh no está en ZIP: exportación, dirección y pinmux deben verificarse
con Ferxxo. Evitar mezclar con PB3 salida LED del firmware DMA anterior.

## Operación real
milkv_stream.capture fija SCLK=0,CS=1,MOSI=0, espera20 ms, baja CS y espera15 ms.
Por cada bit MSB-first: presenta MOSI, espera200 us, sube SCLK, espera200 us, lee
MISO, baja SCLK y espera200 us. En finally libera CS y deja SCLK/MOSI bajos.
slave_transfer espera CS bajo; durante SCLK bajo presenta MISO y espera alto para
leer MOSI, luego espera bajo. Intención modo0 (CPOL0/CPHA0). wait_clock observa
niveles mediante polling: no captura flancos en hardware y puede perder transiciones.
Transferencia full-duplex264 B. Primer byte MOSI es preset; resto ceros. No hay
interrupción SPI ni HAL_SPI; acceso GPIO directo en STM32, sysfs+sleep en Python.

```text
STM32: prepare_frame(captura) ── espera CS ── transmite ventana previa ─ captura siguiente
MilkV: CS=1,20ms ─ CS=0,15ms ─ 264 bytes / 2112 clocks ─ CS=1 ─ pausa restante
MOSI:                      preset nuevo + 263 bytes cero
MISO:                      SC + estado/preset previo + muestras + CRC
```
El nuevo preset se aplica DESPUÉS de transmitir. No hay ACK ni READY externo.
La cadencia de4 s se mide desde inicio de capture (milkv_stream.main), no desde
final de transferencia. Una transferencia larga reduce/elimina la pausa restante.

## Temporización y bloqueo
No existe frecuencia real medida en la evidencia aportada. Tres sleeps200 us/bit
solicitan al menos1.2672 s para2112 bits antes de syscalls, scheduler y setup;
~1667 bit/s es límite ideal por esos retardos, no tasa validada ni1 MHz.
Una pausa Linux >100 ms provoca timeout de wait_clock. Sin embargo slave_transfer
espera CS alto indefinidamente tanto en éxito como abort: el timeout no recupera
CS atascado. La espera inicial bloquea otras tareas del bucle principal.
prepare_frame no escucha SPI mientras adquiere; 64 periodos a100 Hz requieren
~640 ms nominales. Arranque/reinicio o siguiente transferencia lenta puede empezar
antes de TX listo, perdiendo cabecera. Los15 ms no son un handshake.
MISO sigue salida aunque CS alto: limitación si se comparte bus con más dispositivos.

## Mejoras pendientes, sin implementación
Confirmar SysTick/firmware cargado, obtener preparación GPIO y medir CS/SCLK/MOSI/MISO.
Definir recuperación acotada de CS y sincronización TX lista manteniendo bit-banging.
Medir jitter y latencias bajo carga; conservar CRC y rechazo de tramas inválidas.
STM32 SPI periférico hardware podría estudiarse después con Milk-V aún GPIO,
pero no es requisito de esta integración. Toda prueba física requiere permiso y
confirmación de placas conectadas. Ver estado_firmware para bloqueo SysTick.
