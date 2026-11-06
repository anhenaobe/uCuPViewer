# Osciloscopio por USB-UART sin Ethernet

## Qué hace

- STM32 NUCLEO-L432KC: adquisición A0/A1 y SPI modo 0 por GPIO (firmware experimental).
- Milk-V Duo S: maestro SPI por GPIO, envía datos validados (cabecera + CRC) por la consola UART0 existente.
- PC Debian: lee `/dev/ttyUSB0`, **transfiere en memoria automáticamente el programa capturador a la Milk-V por UART** y abre un dashboard en `http://127.0.0.1:8080`.
- **No usa Ethernet, IP de la Milk-V, `scp`, ni dependencias `pip`**. Python estándar y `stty` bastan en el PC y la Milk-V.

**Importante:** En esta versión el servidor HTTP está en el **PC**, no en la Milk-V, así que todavía **no cumple** el requisito del profesor de servir HTTP desde el SBC. Sirve para confirmar visualización y SPI. Luego será necesario usar un enlace IP (por ejemplo USB RNDIS, sin cable Ethernet físico) y Nginx en el SBC.

## Procedimiento

1. Abre `Prueba_SPI` en VS Code, reemplaza `src/main.c` por `stm32/src/main.c` de esta carpeta. Conserva tu `platformio.ini` que ya funciona. Ejecuta `pio run -t upload`.
2. Mantén los 5 cables SPI existentes: B13↔PB5, B14↔PB4, B15↔PB3, B16↔PA4, GND↔GND. Para una prueba segura, STM 3V3→10kΩ→A0, A1→GND.
3. Abre Minicom en el PC: `sudo minicom -D /dev/ttyUSB0 -b 115200 -8`. Entra a Debian de la Milk-V como root. Si U-Boot se detiene, ejecuta `sysboot mmc 0:1 any ${pxefile_addr_r} /extlinux/extlinux.conf`.
4. En la Milk-V, ejecuta `cd ~/osciloscopio/spi && ./preparar_gpio.sh`. Tiene que terminar con `CONFIGURACION TERMINADA`.
5. **Cierra Minicom** con `Ctrl+A`, `X` (acepta salir). Deja ambas placas encendidas.
6. En el PC Debian, dentro de `pc/`, ejecuta `sudo python3 pc_dashboard_uart.py --serial /dev/ttyUSB0`.
7. Abre en el navegador del PC `http://127.0.0.1:8080`. Selecciona 100, 1000 o 10000 Sa/s; la ventana se renueva cada 4 s.
8. Para detener, `Ctrl+C` en la terminal PC. Para recuperar Minicom, vuelve a abrirlo. El capturador de la Milk-V se carga **en memoria**; al reiniciar la Milk-V, repite desde el paso 3.

## Si falla

- `No existe /dev/ttyUSB0`: revisa `ls /dev/ttyUSB* /dev/ttyACM*` en el PC.
- `Sin respuesta SCOPE_UID:0`: la sesión de root no quedó abierta cuando cerraste Minicom; vuelve a entrar a root desde Minicom y sal sin apagar la Milk-V.
- `Cabecera incorrecta`, `CRC`: el dashboard **no dibuja datos falsos**; el firmware, las conexiones SPI o la sincronización todavía necesitan corrección.
- Para ver la interfaz de forma aislada, usa `python3 pc_dashboard_uart.py --demo`; mostrará `DEMO SIMULADA` y no usará UART.

## Limitaciones técnicas

- No se ha probado físicamente en tus placas; no se debe asumir que el protocolo funcionará hasta recibir muestras reales.
- La captura a 100, 1000 y 10000 Sa/s es nominal, la precisión debe verificarse. La captura tiene 64 instantes por canal, pero no utiliza disparo ADC+DMA.
- El SPI es GPIO (software) y la velocidad de intercambio debe medirse experimentalmente.
- No conectar voltajes negativos ni mayores de 3.3V al ADC.
