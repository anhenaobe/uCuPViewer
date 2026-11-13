# Resultados de pruebas SPI, infraestructura y red

**Proyecto:** uCuPViewer — adquisición y visualización STM32 / Raspberry Pi  
**Responsable:** Ferxxo — infraestructura Linux y enlace SPI  
**Estado:** plantilla de registro; no contiene resultados medidos  
**Commit probado:** pendiente  
**Fecha del ensayo:** pendiente

Completar durante pruebas físicas y de red. Mantener `NOT_RUN` mientras una prueba no se ejecute. No marcar una medición como verificada solo porque exista una configuración o un simulador. El contrato v0.2 sigue siendo una propuesta; valores de trama, estados, READY y tiempos deben confirmarse con los responsables antes de dar PASS.

Referencias: [contrato de interfaces v0.2](../../docs/03_contratos_interfaces_v0_2.txt), [guía de Ferxxo](../../docs/por_integrante/ferxxo.txt), [checklist de infraestructura](checklist.md).

## 1. Identificación de plataforma y sistema operativo

| Parámetro | Valor ensayado / registrado | Comando o nota de verificación |
|---|---|---|
| Modelo SBC | Raspberry Pi 4 Model B — modelo seleccionado; confirmar unidad ensayada | Verificar físicamente y registrar revisión |
| Sistema operativo | Pendiente | `cat /etc/os-release` |
| Kernel y arquitectura | Pendiente | `uname -a`; `uname -m` |
| Dispositivo SPI | Pendiente (`/dev/spidev0.0` es candidato) | `ls -l /dev/spidev*` |
| Usuario del backend | Pendiente (`ucupviewer`, según plantilla) | `id ucupviewer` |
| Grupos y permisos del nodo SPI | Pendiente; no inferir de la configuración | `id ucupviewer`; `stat /dev/spidev0.0` |
| Versión de Python y paquete spidev | Pendiente | `python3 --version`; `dpkg-query -W python3-spidev` |
| Versión de Nginx | Pendiente | `nginx -v` |

## 2. Verificación de hardware y mapa de pines

Los pines de la columna Raspberry Pi/STM32 son una **propuesta por revisar**, no un pinout aprobado. Valeria y Andrew deben validar señales, ruta SPI del STM32L432KC, conflictos con ADC/LED y continuidad antes de energizar. Confirmar niveles eléctricos con el montaje real.

| Señal | Raspberry Pi 4, header de 40 pines (propuesta) | STM32L432KC (propuesta) | Nivel / polaridad esperados | Estado / observación |
|---|---|---|---|---|
| SPI_CS / CE0 | GPIO 8, pin físico 24 | PA4 (NSS), por confirmar | 3,3 V, activo bajo | NOT_RUN; confirmar ruta y selección de CS |
| SPI_SCLK | GPIO 11, pin físico 23 | PA5, por confirmar | 3,3 V | NOT_RUN; medir en ambos extremos |
| SPI_MISO | GPIO 9, pin físico 21 | PA6, por confirmar | 3,3 V | NOT_RUN; confirmar dirección MCU→Pi |
| SPI_MOSI | GPIO 10, pin físico 19 | PA7, por confirmar | 3,3 V | NOT_RUN; confirmar dirección Pi→MCU |
| GPIO_READY (opcional) | GPIO 25, pin físico 22 (propuesta) | PB0 / pin acordado (pendiente) | 3,3 V; significado/polaridad pendientes | NOT_RUN; no usar hasta acordar handshake |
| GND | Pin físico 6 (ejemplo; comprobar montaje) | GND | Tierra común | NOT_RUN; confirmar continuidad |

**Verificación por:** Valeria: pendiente · Andrew: pendiente · Fecha: pendiente  
**Placa/revisión STM32 y montaje:** pendiente  
**Instrumento / método / evidencia (foto o diagrama):** pendiente

## 3. Pruebas de protocolo y comunicación SPI

Registrar dispositivo (`/dev/spidevB.C`), modo, bits por palabra, orden de bits, CS, frecuencia solicitada, firmware SHA y versión del módulo Python. Los estados de ACK se registran como byte bruto hasta que el equipo apruebe su mapa. La respuesta simultánea durante CMD no sustituye la transacción separada de ACK.

### 3.1 PING (opcode candidato `0x01`) y ACK

- Iteraciones solicitadas: 100
- CMD candidato: `[0xA5, 0x01, 0x00, seq, 0x00, 0x00, CRC_LO, CRC_HI]`
- Secuencia usada / rango: pendiente
- ACK observado (bytes o archivo de captura): pendiente
- CRC de CMD/ACK validado en: ____ / ____ iteraciones
- Ecos de opcode y secuencia válidos en: ____ / ____ iteraciones
- Porcentaje de éxito: ____ %
- Errores CRC / longitud / secuencia / timeout: ____ / ____ / ____ / ____
- Estado: `NOT_RUN` / `PASS` / `FAIL` / `BLOCKED`
- Evidencia, firmware y commit: pendiente

No asumir que `status=0` significa `OK` hasta aprobar el mapa de estados del contrato.

### 3.2 Ventanas `READ_WINDOW` (268 bytes)

- Iteraciones solicitadas: 100 ventanas consecutivas
- Transacciones observadas: CMD `READ_WINDOW` → ACK → transferencia de 268 bytes con dummy bytes; tiempos/READY según acuerdo firmado
- Longitud recibida por ventana: pendiente; esperado por el formato candidato: 268 bytes
- Campos verificados: sync `0x5A`, secuencia, 64 muestras/canal, 256 bytes de payload, CRC, padding y rango ADC acordado
- Ventanas con CRC correcto: ____ / 100
- Ventanas con secuencia correcta: ____ / 100
- Bytes corruptos / ventanas perdidas / errores: ____ / ____ / ____
- Estado: `NOT_RUN` / `PASS` / `FAIL` / `BLOCKED`
- Evidencia, firmware y commit: pendiente

La decodificación esperada del payload candidato es 128 valores `uint16` little-endian intercalados: `[CH1_0, CH2_0, CH1_1, CH2_1, ...]`, 64 por canal. El simulador `MockSPIDevice` no cuenta como evidencia física.

## 4. Medición física del reloj SCLK

Medir con osciloscopio o analizador lógico y guardar la configuración del instrumento, sonda, punto de conexión y captura. La frecuencia configurada en `spidev` no equivale a la frecuencia física medida.

| Frecuencia solicitada | Frecuencia medida | SCLK alto / bajo | Calidad / observaciones | Estado |
|---:|---:|---:|---|---|
| 1 MHz | Pendiente | Pendiente / pendiente | Pendiente | `NOT_RUN` |
| 2 MHz | Pendiente | Pendiente / pendiente | Pendiente | `NOT_RUN` |
| 4 MHz | Pendiente | Pendiente / pendiente | Pendiente | `NOT_RUN` |
| 8 MHz | Pendiente | Pendiente / pendiente | Pendiente | `NOT_RUN` |

**Instrumento y modelo:** pendiente · **Ancho de banda / sonda:** pendiente · **Fecha:** pendiente · **Archivos de captura:** pendiente

## 5. Pruebas HTTP, proxy Nginx y acceso de red

No publicar una IP privada real en este documento. Usar un hostname o marcador; guardar detalles locales sensibles fuera de Git.

| Verificación | Resultado observado | Estado / evidencia |
|---|---|---|
| Nginx escucha en HTTP/80 | Pendiente | `NOT_RUN` |
| `/` sirve los archivos reales del dashboard | Pendiente; requiere `frontend/index.html` | `NOT_RUN` |
| `/api/` llega al backend en loopback | Pendiente; puerto 5000 es provisional hasta acordarlo con Pipe | `NOT_RUN` |
| Código HTTP y endpoint probados | Pendiente; registrar ruta, método, código y cuerpo sin datos sensibles | `NOT_RUN` |
| Acceso desde segundo equipo de la misma LAN | URL de ejemplo: `http://<hostname-o-IP-de-prueba>/` | `NOT_RUN` |
| Intervalo real de refresco en navegador | Pendiente; objetivo de contrato: 1–4 s, inicialmente 2 s | `NOT_RUN` |
| MCU desconectado / fallo SPI visible en dashboard | Pendiente; registrar aviso, timeout y logs | `NOT_RUN` |

**Cliente de prueba / navegador / fecha:** pendiente  
**Backend/frontend SHA:** pendiente  
**Resultado de conexión desde otro dispositivo:** pendiente

## 6. systemd y arranque automático

`backend/main.py` y el entrypoint systemd ya están integrados en modo simulado. El despliegue y arranque en la Raspberry Pi siguen sin ejecutarse; mantener `NOT_RUN` hasta registrar evidencia en la placa. La integración de simulación no demuestra SPI físico.

| Servicio | `systemctl status` | Habilitado al inicio | Logs revisados | Estado / evidencia |
|---|---|---|---|---|
| `nginx.service` | Pendiente | Pendiente | Pendiente | `NOT_RUN` |
| `ucupviewer-backend.service` | Plantilla y backend simulado integrados; despliegue pendiente | Pendiente | Pendiente | `NOT_RUN` |

- Validación de config Nginx (`nginx -t`): pendiente
- Reinicio de la Pi y hora de prueba: pendiente
- Servicios tras reinicio: pendiente
- `journalctl -u nginx -b` / `journalctl -u ucupviewer-backend -b`: pendiente
- Versión de SO, Nginx, backend y commit: pendiente

## 7. Firmas de verificación y aprobación

| Rol | Nombre | Alcance revisado | Firma / fecha |
|---|---|---|---|
| Infraestructura / SPI | Ferxxo | Configuración Pi, permisos, SPI y proxy | Pendiente |
| Hardware | Valeria | Pinout, niveles, tierra y montaje | Pendiente |
| Firmware | Andrew | Transacciones SPI, secuencia y preparación TX | Pendiente |
| Backend | Pipe | API, puerto local, entrypoint y estados | Pendiente |
| QA | Checho | Criterios, mediciones y evidencia | Pendiente |

**Observaciones y pendientes para la siguiente sesión:**

- Pendiente completar inventario y confirmar pinout físico.
- Pendiente aprobar el mapa de estados SPI y el handshake ACK/READY/READ_WINDOW.
- Pendiente acordar el puerto del backend y el entrypoint systemd.
- Pendiente ejecutar y adjuntar evidencias físicas y de red.
