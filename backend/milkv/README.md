# uCuPViewer | Backend de Milk-V Duo S (prototipo UART)

**Estado:** prototipo para revisión del equipo. No se ha probado físicamente Milk-V ↔ STM32. No sustituye el contrato de enlace SPI v0.2 del repositorio sin aprobación.

Esta carpeta es exclusivamente el trabajo del **backend**: protocolo de transporte serial UART, simulación, manejo de ventanas ADC de 2 canales y API HTTP. El firmware STM32 existente en `firmware/stm32/` NO fue modificado. El frontend y los archivos de infraestructura tampoco.

## Requisitos

- Milk-V Duo S con Debian y Python 3 (o Linux de desarrollo para simulación).
- Python estándar, sin paquetes `pip` de terceros.
- Para UART real: dispositivo UART operativo y permisos de acceso; `/dev/ttyS2` es *candidato*, no está habilitado en la imagen Debian observada.
- Firmware del STM32 compatible con la trama UART descrita abajo. **El firmware ADC/DMA existente en main todavía no habla este protocolo UART.**

## Uso

Desde `backend/milkv/`:

```bash
# Prueba independiente del hardware: datos simulados
python3 server.py --simulate --host 127.0.0.1 --port 8080

# Solo DESPUÉS de habilitar/probar UART2 y cargar firmware UART compatible
python3 server.py --device /dev/ttyS2 --host 127.0.0.1 --port 8080
```

Con el servidor simulado funcionando, desde otra terminal:

```bash
curl -i http://127.0.0.1:8080/api/v1/status
curl -i http://127.0.0.1:8080/api/v1/window/latest
curl -i -X POST http://127.0.0.1:8080/api/v1/acquisition/preset \
  -H 'Content-Type: application/json' -d '{"sample_rate_hz":1000}'
```

Para publicar HTTP en otro host de la red local puedes usar `--host 0.0.0.0` dentro de una red de laboratorio confiable. El servidor integrado de Python es **solo de desarrollo**; el archivo `nginx-ucupviewer.conf` es un ejemplo para revisión, no se instala automáticamente.

## API HTTP (propuesta para coordinar con frontend)

- `GET /api/v1/status`: estado, `source`, `session_id`, `config_revision`, frecuencia.
- `GET /api/v1/window/latest`: ventana ADC completa o HTTP 204 sin cuerpo si el proveedor está disponible sin ventana válida.
- `POST /api/v1/acquisition/preset`: cuerpo `{"sample_rate_hz":100|1000|10000}` y respuesta con `applied=true` solo cuando el proveedor activo acepta el cambio. **Simulated no equivale a ACK del MCU.**

Errores con JSON `{"error":{"code":"...","message":"...","details":null}}`. Existe manejo básico de 422, 503 y 504, pero quedan pendientes las pruebas físicas de desconexión, recuperación y el mapeo correcto de `BusyError` a 409 cuando el MCU está ocupado. `is_stale` usa 6000 ms como valor **provisional**. No asegurar operación a 40000 Sa/s.

## Protocolo UART propuesto (pendiente de aprobación de firmware)

- UART 115200 baudios, 8N1, lógica de 3,3 V en el conector elegido de Duo S.
- CMD de 8 bytes: `[A5,opcode,arg,seq,0,0,CRC16_LE]`.
- ACK de 8 bytes: `[5A,status,opcode_echo,seq_echo,info0,info1,CRC16_LE]`.
- Comandos: PING=1, SET_PRESET=2, START_CAPTURE=3, GET_STATUS=4, READ_WINDOW=5.
- IDs de preset: 0=100, 1=1000, 2=10000 Sa/s por canal.
- READ_WINDOW: 268 bytes; metadatos + 64 pares ADC (128 × uint16 little-endian, 256 bytes) + CRC16-CCITT-FALSE + padding.
- Serialización de operaciones sobre UART en backend. Capturas bajo demanda, no transmisión continua sin pérdidas garantizada.

## Configuración física pendiente

En los logs reales de la Milk-V Duo S, `/proc/tty/driver/serial` mostraba UART0 y UART4 activos, pero UART2 (`ttyS2`) como `uart:unknown`. El `duo-pinmux` instalado listaba nombres `GP0...` de otra variante. **No ejecutar** el script de pinmux hasta habilitar UART2 en el kernel/device tree correcto y disponer de `duos-pinmux` propio de la Duo S. `configure_uart2_duos.sh` aborta si no se cumplen esas verificaciones; no modifica el DTB. Antes de unir las placas, `loopback_uart2.py` permite una prueba local con TX/RX puenteados (desconectados del STM32).

### Conexiones físicas propuestas (revisar antes de cablear)

Milk-V Duo S J3: B11/UART2 TX → STM32 PA10/USART1 RX; B12/UART2 RX ← STM32 PA9/USART1 TX; GND ↔ GND. Solo señales UART TTL compatibles, alimentación de placas por separado. Revisar el pinout concreto con hardware antes de ejecutar pruebas; no usar pines J4 de 1,8 V como si fueran de 3,3 V.

## Pruebas de software

Desde la raíz del repositorio:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s backend/tests -v
```

Se ejecutaron 7 pruebas con resultado OK en Linux de desarrollo (2026-11-03): CRC, comando/ACK, ventana, HTTP simulado y pseudoterminal UART. **No son evidencia de comunicación física**, ni de temporización real del ADC.

## Integración pendiente

- Revisar/congelar un contrato **UART** con Andrew (firmware), Mateo (frontend), Ferxxo (infraestructura), Valeria (pinout) y Checho (QA). La propuesta v0.2 actual en `docs/` describe Raspberry Pi + SPI; no se ha editado desde esta entrega de backend.
- Probar firmware compatible y el pinmux real de Duo S; validar CRC, ACK, timeouts, BUSY, nuevas ventanas y reinicios.
- Añadir despliegue systemd/Nginx y pruebas hardware solo con evidencia obtenida del dispositivo.
