# uCuPViewer | Backend SPI para Milk-V Duo S

**Estado: prototipo en revisión. No se ha validado SPI entre las dos placas.**

Este cambio se limita a `backend/`; no edita el firmware de Andrew, el frontend ni el contrato compartido en `docs/`. La rama principal mantiene intactos los archivos del equipo. Esta propuesta vuelve a la **topología SPI maestro/esclavo** del contrato v0.2, sustituyendo la Raspberry Pi por Milk-V Duo S.

## 1. Arquitectura y responsabilidades

- **STM32L432KC:** captura ADC de dos canales, TIM2 + DMA y (por implementar con Andrew) una máquina de estados SPI esclavo.
- **Milk-V Duo S:** SPI maestro, validación CRC16/seq/longitud, ventanas coherentes y API HTTP.
- **Frontend:** `/api/v1/status`, `/api/v1/window/latest`, `/api/v1/acquisition/preset`.

El firmware de STM32 presente en `firmware/stm32` **todavía no implementa** SPI esclavo; la verificación física depende de esa integración.

## 2. Ejecutar sin hardware

Desde `backend/milkv/`, con Python >=3.9 (sin dependencias externas para modo simulado):

```bash
python3 server.py --simulate --host 127.0.0.1 --port 8080
```

En otra terminal:

```bash
curl -i http://127.0.0.1:8080/api/v1/status
curl -i http://127.0.0.1:8080/api/v1/window/latest
curl -i -X POST http://127.0.0.1:8080/api/v1/acquisition/preset \
  -H 'Content-Type: application/json' \
  -d '{"sample_rate_hz":1000}'
```

`source=simulated` identifica muestras sintéticas. No atribuir sus ACK ni su temporización al STM32.

## 3. Verificar soporte SPI de Linux antes de conectar cables

La placa identificada por el usuario es **Milk-V Duo S con Debian**, no Duo original. El puerto `/dev/spidev3.0` es **solo un ejemplo**, nunca un nodo confirmado. Ejecutar en la Milk-V:

```bash
sh check_spi_duos.sh
ls -l /dev/spidev*
cat /proc/device-tree/model
```

Si no aparece `/dev/spidevX.Y`, falta habilitar el controlador SPI / pinmux / spidev en la imagen Debian correspondiente. **No** ejecutar cambios automáticos de Device Tree a ciegas. El script solo inspecciona el sistema. Verificar además `python3 -c 'import spidev'`; si falta y hay conexión a repositorios, instalar con `apt install python3-spidev`.

**Pinout J3 oficial para la Milk-V Duo S (nivel 3.3 V):**

| J3 | Duo S | Dirección del maestro | Señal hacia STM32 |
|---|---|---|---|
| pin 19 | B13, SPI3_SDO | salida | STM32 MOSI / SPI_MOSI |
| pin 21 | B14, SPI3_SDI | entrada | STM32 MISO / SPI_MISO |
| pin 23 | B15, SPI3_SCK | salida | STM32 SCK |
| pin 24 | B16, SPI3_CS | salida, activo bajo | STM32 NSS |
| pin 20 | GND | referencia | STM32 GND |

**NO asumir pines STM32 concretos hasta que Andrew y Valeria confirmen pinmux, conflicto con PA0/PA1 ADC, PB3 LED y SWD.** No conectar 5V de una placa a entradas 3.3V de la otra. Compartir solo GND y señales compatibles; alimentación independiente.

Fuente: https://milkv.io/docs/duo/getting-started/duos

## 4. Ejecutar en SPI hardware, después de habilitar spidev y flashear STM32 SPI

```bash
python3 server.py --device /dev/spidevX.Y --spi-speed-hz 1000000 \
  --spi-ack-delay-ms 5 --host 127.0.0.1 --port 8080
```

Sustituir `X.Y` por el bus y CS realmente presentes. La transferencia se realiza en 3 transacciones independientes, con CS liberado entre ellas: 8 bytes CMD, 8 bytes ACK y, solo para READ_WINDOW, 268 bytes de ventana. El STM32 debe preparar cada respuesta antes de que Linux genere los relojes. `ack-delay-ms=5` es provisional: sin GPIO READY no se garantiza el instante correcto para leer.

- SPI modo 0 (CPOL 0, CPHA 0), MSB first, 8 bits, **SCLK inicial 1 MHz** (no máximo medido).
- CRC-16/CCITT-FALSE y secuencia de 8 bits.
- Pares intercalados 64×CH1 + 64×CH2, ADC RAW de 12 bits almacenado uint16 little-endian.
- Comandos candidatos: PING=1, SET_PRESET=2, START_CAPTURE=3, GET_STATUS=4, READ_WINDOW=5.
- Frecuencias: 100, 1000 y 10000 Sa/s **por canal**. 40000 requiere verificación adicional.

**Aún debe acordarse con firmware:** valores no-OK de status, significado exacto de info0/info1 en ACK, GET_STATUS (este prototipo supone 0=idle, 1=capturing, 2=ready, 3=error), ciclo de CS, preparación TX y estrategia READY/IRQ. No se garantiza compatibilidad con el STM32 actual hasta validar el protocolo.

## 5. API HTTP mantenida para frontend

`GET /api/v1/status`: `connected`, `capture_status`, `source`, `session_id`, `config_revision` y frecuencia actual.

`GET /api/v1/window/latest`: HTTP 200 y ventana con `window_id`, `captured_at`, `is_stale` (umbral provisional 6000 ms), frecuencia y 64 muestras por canal; 204 sin cuerpo cuando aún no existe ventana válida y el proveedor está disponible.

`POST /api/v1/acquisition/preset`: solo indica `applied:true` al recibir confirmación del proveedor real; simulación se etiqueta `source=simulated`.

Respuestas de error uniformes `{"error":{"code":"...","message":"...","details":null}}`; 409 ocupado, 422 preset no válido, 503 hardware/protocolo no disponible, 504 timeout.

## 6. Pruebas de software

Desde la raíz del repositorio:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s backend/tests -v
```

Incluye pruebas de framing, CRC, API HTTP simulada y periférico SPI **falso** que verifica secuencias de tres transferencias. Ninguna constituye prueba de cableado, señal READY, pinmux Linux o temporización real.

## 7. Límites de entrega

Este backend usa `spidev` solo en modo hardware y se ejecuta en el servidor HTTP integrado de Python **para desarrollo**. Para entrega final, Nginx/Apache deberá servir el dashboard y hacer proxy de `/api/` al servicio, de acuerdo con el contrato. `nginx-ucupviewer.conf` es un ejemplo no instalado. Añadir systemd, pruebas de reconexión, límites experimentales y pruebas de carga es trabajo pendiente.

No fusionar este PR hasta revisión de firmware, backend, frontend y QA.
