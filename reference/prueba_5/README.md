# Osciloscopio híbrido STM32L432KC + Milk-V Duo S

**Estado: implementación integral reproducible, software verificado con pruebas unitarias, integración física aún por verificar en las placas.** Los resultados de un sistema embebido no se pueden garantizar sin compilar el firmware en tu PlatformIO, medir la señal y probar el cableado. Este repositorio nunca presenta datos ficticios como si fueran reales.

## 1. Arquitectura

- **STM32** (PlatformIO, `framework=stm32cube`): ADC1 canales PA0/PA1, conversión secuencial disparada por TIM2 (100/1000/10000 Sa/s **por canal**) y DMA circular. Una interrupción EXTI implementa SPI software esclavo modo 0 en los pines de siempre.
- **Milk-V Duo S** (Debian Forky): SPI software maestro por GPIO sysfs en C compilable con gcc, respaldo Python si no hay gcc, 64 pares de muestras, CRC16, aplicación HTTP en Python stdlib, servicio `systemd`, **Nginx en la propia Milk-V**.
- **PC Debian**: se programa la STM32 con ST-LINK, se instala Milk-V por la consola USB/UART de siempre y se abre el dashboard por **USB-C de datos de Milk-V como interfaz de red USB**. No se requiere cable Ethernet.

El convertidor **USB/UART es la consola y el método de carga de archivos**; no es por sí solo una interfaz IP para navegar a Nginx. Si se exige que los datos viajen *solo* por el adaptador UART, habría que añadir una red PPP/SLIP o un túnel serial y no puede garantizarse sin una configuración adicional. En esta guía, el tráfico HTTP viaja por USB-C de datos (USB gadget), y no por Ethernet.

### Cableado mantenido

| Enlace | Milk-V Duo S J3 | STM32 NUCLEO-L432KC |
|---|---|---|
| MOSI | Pin físico 19 / XGPIOB13 / GPIO461 | D11 / PB5 (entrada) |
| MISO | Pin físico 21 / XGPIOB14 / GPIO462 | D12 / PB4 (salida) |
| SCLK | Pin físico 23 / XGPIOB15 / GPIO463 | D13 / PB3 (entrada) |
| CS activo en 0 | Pin físico 24 / XGPIOB16 / GPIO464 | A3 / PA4 (entrada) |
| GND | Pin físico 25 | GND |
| Canal 1 | — | A0 / PA0, solo 0–3.3V |
| Canal 2 | — | A1 / PA1, solo 0–3.3V |

Ambas placas se alimentan por separado, con **GND común**. No conectes TX/RX de UART a los pines SPI. Conecta USB/UART al J3 UART0 **como ya lo hiciste para Minicom** (TX/RX cruzados, solo GND, sin 5V). No conectes señales negativas a A0/A1.

### Conexión de prueba ADC

Con placas apagadas, STM32 **3V3 → resistencia de 10kΩ → A0**, STM32 **GND → A1**. Al capturar esperamos A0 cerca de 4095 (≈3.3 V) y A1 cerca de 0. Los valores exactos dependen de VDDA y el ruido.

## 2. Programar STM32 desde PlatformIO — NO usar Arduino IDE

Descomprime este proyecto en el computador Debian. Abre **la carpeta `stm32` de este ZIP como proyecto PlatformIO** (VS Code → File → Open Folder). No mezcles este `main.c` con versiones anteriores.

```bash
cd ~/Downloads/osciloscopio_final/stm32   # ajusta la ruta real
pio run
pio run -t upload
```

Debe indicar `SUCCESS` y `Verified OK`. El `platformio.ini` incluido usa el protocolo custom OpenOCD que resuelve la incompatibilidad anterior con `hla_swd`, y usa el ELF con la dirección FLASH embebida. Si alguna ruta de OpenOCD difiere en tu PC, puedes conservar **tu `platformio.ini` que ya programó correctamente** y usar el nuevo `src/main.c`.

Comprueba que la STM32 esté encendida tras cargarlo. No es necesario enviar comandos seriales a la STM32; ésta procesa comandos SPI del SBC.

## 3. Instalar Milk-V **solo mediante USB/UART**, sin Ethernet ni scp

1. En tu computador Debian, abre Minicom para verificar que existe un shell `root@duos:~#` en Milk-V:

```bash
sudo minicom -D /dev/ttyUSB0 -b 115200 -8
```

2. Si el arranque quedó en `cv181x_c906#`, usa el comando que ya conoces:

```text
sysboot mmc 0:1 any ${pxefile_addr_r} /extlinux/extlinux.conf
```

3. Entra como root. **Sal de Minicom con `Ctrl+A` y luego `Q`**; no desconectes ni apagues la placa. El instalador usa el mismo `/dev/ttyUSB0`.

4. Desde el directorio raíz del ZIP en tu PC, instala por UART:

```bash
cd ~/Downloads/osciloscopio_final  # ajustar ruta
sudo python3 pc/instalar_uart.py --port /dev/ttyUSB0
```

Si indica `Falta pyserial`, instala en el PC `python3-serial` (paquete de Debian) o pyserial dentro de un entorno Python. Este envío comprime los archivos, verifica su SHA256 y los extrae en `/root/osciloscopio_final/milkv` de la Milk-V.

5. **Vuelve a abrir Minicom**:

```bash
sudo minicom -D /dev/ttyUSB0 -b 115200 -8
```

En el shell `root@duos` ejecuta:

```bash
cd /root/osciloscopio_final/milkv
sh instalar.sh
```

Este script prepara el GPIO, compila `spi_master.c` con GCC (si existe) y activa `osciloscopio.service` al arranque. Si falta GCC, usa `spi_master.py` como alternativa automática, **sin afirmar que se compiló C**. Si falta Nginx, hay que instalarlo en cuanto dispongas de red; en ese caso el backend sigue disponible en puerto 8080.

6. Verifica una adquisición desde Minicom:

```bash
cd /root/osciloscopio_final/milkv
python3 app.py --once --preset 2
```

**Antes** de ejecutar una prueba `--once`, detén el servicio para evitar colisión en los GPIO:

```bash
systemctl stop osciloscopio.service
python3 app.py --once --preset 2
systemctl start osciloscopio.service
```

Salida esperada si el hardware está bien: JSON con `"preset":2`, `"rate_hz":1000`, `"samples"` convertidas y 64 pares. Si devuelve `Cabecera incorrecta` o `CRC incorrecto`, no hay datos válidos; revisar estado de STM32 y MISO/CS con multímetro u osciloscopio, no simular ondas.

## 4. Abrir la interfaz HTTP **alojada en la Milk-V** sin cable Ethernet

Tu imagen Debian Forky ya mostró en el arranque `usb-gadget-rndis.service`, `usb0`, `ifup@usb0`. Utilizaremos esa interfaz.

1. **Deja el adaptador USB-UART conectado** para administración. Conecta también el **USB-C de datos/alimentación de la Milk-V a un puerto USB del computador** con un cable USB-C que transfiera datos. Una toma/cable solo de carga no sirve.
2. En Minicom, consulta la IP de la Milk-V:

```bash
ip -br -4 addr show usb0
```

Si existe `usb0` pero no tiene IPv4:

```bash
ip link set usb0 up
ip addr add 192.168.42.1/24 dev usb0
```

3. En el **computador**, ejecuta:

```bash
ip -br link
ip -br -4 addr
```

Busca una interfaz USB de red nueva (por ejemplo `enx...` o `usb0` del PC). Si no recibió IPv4 por DHCP, asígnale `192.168.42.2/24` (sustituye `INTERFAZ_USB`):

```bash
sudo ip link set INTERFAZ_USB up
sudo ip addr add 192.168.42.2/24 dev INTERFAZ_USB
ping -c 2 192.168.42.1
```

No uses `end0`: esa es la Ethernet física que no quieres conectar. La IP `192.168.42.1` es un ejemplo/documentación de Milk-V; usa la IP real de `usb0` cuando sea diferente.

4. Si Nginx ya está instalado, abre `http://192.168.42.1/` en el navegador del PC (o la IP real `usb0` de Milk-V). De lo contrario usa `http://192.168.42.1:8080/` hasta instalar Nginx.

5. Para instalar Nginx mediante repositorios cuando la Milk-V tenga acceso a paquetes:

```bash
apt-get update
apt-get install -y nginx
sh /root/osciloscopio_final/milkv/instalar.sh
```

6. Control y registros:

```bash
systemctl status osciloscopio.service
journalctl -u osciloscopio.service -n 30 --no-pager
nginx -t
systemctl status nginx
```

**Minicom puede permanecer abierto mientras navegas por USB-C**, porque el HTTP ya no usa `/dev/ttyUSB0`: el programa del dashboard se ejecuta en Milk-V como servicio y el PC usa otra interfaz USB de red.

## 5. Protocolo de datos

La comunicación SPI es modo 0, 8 bits MSB first, CS activo bajo, longitud fija **264 bytes**. Los bytes de MOSI son `preset (1/2/3), 0, 0,...`. Cada transferencia envía la última ventana completada, y el comando de preset se aplica a las **capturas siguientes**. MISO:

| Bytes | Contenido |
|---|---|
| 0–1 | ASCII `SC` = 0x53 0x43 |
| 2 | Preset activo (1,2,3) |
| 3 | Estado: 0 OK, 0x20 sin ventana, 0x10...0x17 ADC/timer |
| 4–5 | Secuencia de captura en little endian |
| 6–261 | 64 pares ADC1/ADC2, dos enteros uint16 little endian por par |
| 262–263 | CRC16-CCITT-FALSE sobre bytes 0–261, little endian |

En cada respuesta HTTP se incluyen el estado de la última trama y la tasa efectiva SPI (264×8 bits / tiempo). No se grafica un paquete con CRC inválido.

## 6. Tasa SPI vs tasa ADC: no confundir

- **100 / 1.000 / 10.000 Sa/s**: frecuencia de **disparo TIM2 en STM32** para un par de canales (ADC en secuencia). No es la tasa de transferencia SPI.
- **0,25 Hz dashboard**: una transferencia y un refresco cada cuatro segundos. Una ventana de 64 muestras a 100 Sa/s dura ≈0,64s; a 1.000, ≈0,064s; a 10.000, ≈0,0064s.
- **SPI software sysfs**: en las pruebas anteriores se observaron aproximadamente 1.400–1.470 bit/s efectivos con paquetes de 260 bytes; son mediciones del **prototipo anterior**, no de este firmware final. El programa muestra el nuevo valor real cuando se ejecute.
- **Teórico SPI hardware**: la hoja de datos STM32L432KC indica hasta **37 MHz** de SPI slave full duplex/transmisor bajo condiciones de 2,7–3,6V; hasta **40 MHz** en master. El máximo teórico conjunto queda acotado por `min(fSCK_max_MilkV, 37 MHz, restricciones eléctricas y de firmware)`. La tasa máxima del controlador SPI3 del SG2000 **no se ha verificado con una fuente técnica específica**; no se debe inventar. Este proyecto no usa el controlador físico porque el kernel instalado tiene `CONFIG_SPI=n`.
- **Límite honesto**: la implementación satisface la interfaz lógica SPI y permite demostrar el flujo de datos, pero no acredita las **altas tasas** propias de SPI hardware ni la bonificación ≥40.000 Sa/s. Para eso requeriría migrar el maestro al controlador hardware y validar con instrumentos.

## 7. Pruebas / documentación / entregables

```bash
# En PC, sin hardware:
python3 -m unittest discover -s tests -v
```

Completa estos archivos **con resultados reales**:

- `docs/MATRIZ_VERIFICACION.csv`: pruebas de gabinete y registro de cumplimiento.
- `docs/ARQUITECTURA.md`: diagrama de bloques y flujo, límites de temporización.
- `docs/ROLES_Y_APORTES.md`: equipo de máximo 6 participantes y aportes por integrante.
- `docs/DECLARACION_USO_IA.md`: modelo, tareas, metodología de verificación, enlaces o exportaciones de chats.
- `docs/VIDEO_GUIA.md`: guion para video demostrativo.

Crea el repositorio Git en tu PC:

```bash
git init
git add .
git commit -m 'Osciloscopio hibrido STM32 Milk-V: firmware, SPI, dashboard y pruebas'
```

No incluye videos inventados, resultados de osciloscopio ficticios, ni reportes de pruebas físicas no ejecutadas.

## 8. Si algo falla

- `python3: can't open file pc_dashboard_uart.py`: ese script es de versiones anteriores. **No usarlo.** Todo corre desde `milkv/app.py` en la Milk-V.
- `00 00 00` o `53 53 53`: la STM32 no entrega trama SPI válida; no es un fallo de HTTP. Confirmar **que cargaste el `stm32/src/main.c` de ESTE proyecto**, comprobar GND, CS A3/PA4, MISO PB4/D12, y capturar SCK/CS/MISO con instrumento.
- `SPI timeout`: bajar retardo / reducir procesos que bloqueen la Milk-V, o revisar conexiones; no acusar al ADC sin registros.
- `http://192.168.42.1` no abre: verificar **interfaz usb0** en ambos dispositivos y que USB-C transporta datos; comprobar el servicio.
- `nginx: command not found`: instalar Nginx (requiere disponibilidad de paquetes); como prueba temporal usar puerto 8080.
- `No such file` al instalar por UART: abrir la carpeta correcta; `ls stm32/src/main.c pc/instalar_uart.py milkv/app.py`.
