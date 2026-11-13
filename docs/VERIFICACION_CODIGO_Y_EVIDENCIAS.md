# Verificación de código, pruebas realizadas y evidencias — uCuPViewer


> **Actualización de auditoría GitHub (2026-11-05, hora de Colombia):** se contrastó el contenido de este paquete con `main` en [`af58fc557934`](https://github.com/anhenaobe/uCuPViewer/commit/af58fc55793495d0e4d527ebfa83273e8443e33f). Las referencias al commit `41601d45f7` permanecen deliberadamente como **fuentes históricas exactas** de los ensayos ya documentados. Entre ambas revisiones se incorporaron `reference/prueba_1` a `reference/prueba_6`; son variantes, propuestas o paquetes de pruebas y **NO** permiten cambiar estados a PASS sin un registro experimental trazable. Véase [AUDITORIA_CAMBIOS_GITHUB.md](AUDITORIA_CAMBIOS_GITHUB.md).

**Revisión de fuentes:** `main`, commit [`41601d45f7`](https://github.com/anhenaobe/uCuPViewer/commit/41601d45f71fb994444670fc85fe28a7be1d0a50), 2026-11-05. Este documento es el vínculo entre [matriz](MATRIZ_VERIFICACION.md), implementación, registros de laboratorio y video. **Los fragmentos son extractos localizados del repositorio, no ensayos nuevos realizados al redactar el documento.**

## 1. Reglas de evidencia y criterio de aceptación

Para cada criterio se distinguen cuatro hechos:

1. **Existe código:** archivo, función, commit y líneas verificables; no demuestra que se ejecute en placa.
2. **Se ejecutó prueba:** instrumento/comando, fecha, versión, responsables y registro original.
3. **Hubo resultado positivo o incidente:** describir exactamente condiciones y límites; no transformar resultados de prueba parcial en aceptación total.
4. **Se conserva evidencia:** enlace GitHub, fichero bruto en `tests/evidence/` o video accesible con permisos adecuados.

**No se ha identificado en `main` un video de las tres frecuencias obligatorias**. La sección 8 reserva el enlace de Drive sin inventar URL.

## 2. Trazabilidad de implementación con fragmentos de código

### COD-01 — Tres presets y temporizador TIM2 (`RV-05..08`)

**Ubicación:** [`firmware/stm32/spi_polling/src/main.c`, `rate_hz()` y `prepare_frame()`](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c#L170).

```c
static uint32_t rate_hz(void)
{
    return (preset == 1u) ? 100u : (preset == 3u) ? 10000u : 1000u;
}

uint32_t period_us = 1000000u / rate_hz();
htim2.Init.Prescaler = 15; /* 16MHz / 16 = 1 MHz */
htim2.Init.Period = period_us - 1u;
```

**Demuestra:** códigos para las tres tasas y el cálculo de períodos nominales 10.000/1.000/100 µs. **No demuestra:** tasa real, jitter ni ausencia de períodos perdidos. Para eso se requiere `F-AD03` y `F-AD04`.

### COD-02 — Captura de dos canales y detección de período perdido (`RV-02..04`, `RV-08`, `RD-06`)

**Ubicación:** [`firmware/stm32/spi_polling/src/main.c`, alrededor de las líneas 210–229](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c#L210).

```c
uint8_t err = read_adc(ADC_CHANNEL_5, &a); /* PA0/A0 */
if (!err) err = read_adc(ADC_CHANNEL_6, &b); /* PA1/A1 */
if (err) {
    tx_frame[3] = err;
    goto stop_timer;
}
put16(6u + i*4u, a);
put16(8u + i*4u, b);
/* Señala cuando la conversión no acaba antes del siguiente tick. */
if (i < NSAMPLES-1u && __HAL_TIM_GET_FLAG(&htim2, TIM_FLAG_UPDATE)) {
    tx_frame[3] = 0x17u;
    goto stop_timer;
}
```

**Demuestra:** lectura secuencial CH1/CH2, empaquetado intercalado y alarma `0x17`. **No demuestra:** simultaneidad, voltaje de entrada correcto ni precisión temporal. El código ADC+DMA de `firmware/stm32/src/` es otro proyecto conservado, no este firmware activo.

### COD-03 — Cabecera, secuencia y CRC de SC264 (`RV-03/04/10`, `RD-03/04`)

**Ubicación:** [`firmware/stm32/spi_polling/src/main.c`, `prepare_frame()`](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c#L175) y [formato documentado `frame_sc.md`](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/protocol/frame_sc.md).

```c
memset(tx_frame, 0, sizeof(tx_frame));
tx_frame[0] = 0x53;
tx_frame[1] = 0x43;
tx_frame[2] = preset;
tx_frame[3] = 0u;
sequence++;
put16(4u, sequence);
/* Al finalizar la captura: */
put16(DATA_END, crc16(tx_frame, DATA_END));
```

**Demuestra:** serialización y protección CRC en el firmware. **No demuestra:** transferencia física; la prueba independiente es `F-SP01`. En SC264 hay 6 bytes de cabecera, 256 bytes para 64 pares RAW12 codificados en `uint16` y 2 bytes CRC; total 264.

### COD-04 — Maestro SPI GPIO y validación de tramas (`RV-09/10`, `RD-04/09`)

**Ubicación:** [`backend/milkv_uart/milkv_stream.py`, `capture()`](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/backend/milkv_uart/milkv_stream.py#L40).

```python
tx = bytes((preset,)) + bytes(FRAME_LEN-1)
# Tras capturar los bytes recibidos:
if rx[:2] != b'SC':
    raise ValueError('Cabecera incorrecta: ' + bytes(rx[:8]).hex(' '))
if crc16(rx[:-2]) != int.from_bytes(rx[-2:], 'little'):
    raise ValueError('CRC incorrecto: ' + bytes(rx[:8]).hex(' '))
```

**Demuestra:** envío de preset por el primer byte MOSI y rechazo de cabecera/CRC corruptos en software. **No demuestra:** ACK ni sincronización READY, porque este contrato no los implementa. Los tiempos de espera Linux pueden afectar el rendimiento.

### COD-05 — Cambio de preset después de transferir (`RV-09`)

**Ubicación:** [`firmware/stm32/spi_polling/src/main.c`, `main()`](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c#L283).

```c
if (slave_transfer(&new_preset)) {
    if (new_preset >= 1u && new_preset <= 3u) preset = new_preset;
    /* Capturamos DESPUÉS de CS alto, preparando el próximo cuadro. */
    prepare_frame();
}
```

**Demuestra:** la solicitud recibida durante una transferencia afecta la ventana siguiente. El `HTTP 200` de `/api/preset` no prueba por sí solo que el ADC esté muestreando a esa frecuencia. Validar el preset reportado y medir la cadencia real.

### COD-06 — HTTP y separación `source=hardware/demo` (`RV-14`, `RD-07`)

**Ubicación:** [`backend/milkv_uart/pc_dashboard_uart.py`, `handle_data()`](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/backend/milkv_uart/pc_dashboard_uart.py#L87) y [servidor HTTP](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/backend/milkv_uart/pc_dashboard_uart.py#L180).

```python
STATE.update(status='ok', valid=True, error=None, source='hardware',
             measured_preset=rate_code, rate_hz=rate,
             sequence=data['sequence'], samples=samples,
             transfer_s=data['transfer_s'], effective_bps=data['effective_bps'])
```

**Extracto abreviado** de una llamada multilínea real. La ruta `/api/state` devuelve el estado y `/api/preset` solicita el cambio. **Importante:** `rate_hz` se obtiene del mapa de presets, no de un instrumento que mida la cadencia del ADC; los voltajes se calculan asumiendo 3,3 V, no están calibrados.

### COD-07 — Pruebas unitarias existentes (`RV-19`, `RD-04`)

**Ubicación:** [`tests/milkv_uart/test_protocol_offline.py`](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/tests/milkv_uart/test_protocol_offline.py) y [`tests/milkv_uart/test_uart_console.py`](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/tests/milkv_uart/test_uart_console.py).

```python
def test_crc_known_vector(self):
    self.assertEqual(m.crc16(b'123456789'), 0x29b1)

def test_frame(self):
    b = self.frame()
    self.assertEqual(len(b), 264)
    r = self.capture(b)
    self.assertEqual(r['ch1'], list(range(64)))
```

**Demuestra por construcción:** los tests comprueban CRC conocido, longitud y decodificación simulada. La evidencia previa de [12 tests OK](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_dashboard_uart_validacion.md) es de otra sesión; no se han repetido aquí. **No sustituye** mediciones físicas.

## 3. Evidencia SPI física existente (`F-SP01`, `F-SP02`, `F-SP03`)

Fuente primaria: [validación física después de corregir SysTick](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_validacion_post_systick.md); el firmware tuvo autorización de Andrew y la imagen previa se respaldó. Datos transcritos del registro, **no obtenidos con una nueva sesión**:

| Ejecución | Comando remoto | Bytes | Secuencia | Parser/CRC | Tiempo total |
|---|---|---:|---:|---|---|
| SPI-01 | `./spi_master 2 200` | 264 | 1 | Válido | 1,783 s |
| SPI-02 | `./spi_master 2 200` | 264 | 2 | Válido | 1,791 s |
| SPI-03 | `python3 -B spi_master.py 2` | 264 | 3 | Válido | Sin tiempo en la tabla citada |

**Resultados permitidos:** existen tres transferencias reales válidas con 64 pares por ventana, secuencias consecutivas y CRC correcto. Las dos transferencias del maestro C reportaron 1.185/1.179 bit/s efectivos, incluidas esperas. **No permitido afirmar:** SCLK medido, 0% de errores en 100 ventanas, tasa ADC real de 1.000 Sa/s, tensión real en PA0/PA1 ni estabilidad de largo plazo.

**Evidencia adicional:** [diagnóstico inicial de SPI](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_spi_diagnostico.md) conserva la investigación de 264 ceros y del SysTick inicial bloqueado. No debe presentarse como estado actual tras la corrección.

## 4. Prueba de integración UART/HTTP (`F-IN01`, `F-WEB01`, `F-IN02`)

Fuente: [validación del dashboard UART](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_dashboard_uart_validacion.md).

- La API `/api/state` respondió con `valid=true`, `source=hardware`, `sequence=12` y `sequence=28`, con 64 muestras y `HTTP 200` para `/` en PC/VM. Capturas #4 y #5 reportaron SPI 2,06 s, distinto del maestro C de la prueba SPI anterior.
- Un registro posterior contó **37 capturas válidas y dos errores de JSON por UART**; se documentó recuperación posterior. No declarar que el enlace está libre de errores.
- Se observó un estado `0x17` usando preset 3 (10.000 Sa/s nominales), seguido de recuperación a preset 2 (1.000 Sa/s nominales). Esto **no** prueba la exactitud de las tasas ni que 10.000 Sa/s funcione de forma sostenida.
- El servidor HTTP validado se ejecutaba en una **VM/PC**, no en Milk-V. No se obtuvo inspección visual de los canvas en ese registro.

## 5. Mediciones físicas pendientes (`F-AD01..05`, `F-SP03`, `F-WEB02`)

| Ensayo | Preparación mínima | Dato objetivo que debe registrarse | Estado al generar documento |
|---|---|---|---|
| 100 Sa/s | Dos señales conocidas, preset 1, adquisición de 64 pares | 10 ms nominal entre muestras **por canal**, 64 pares y dispersión medida | PENDIENTE |
| 1.000 Sa/s | Señales conocidas, preset 2, 64 pares | 1 ms nominal, error/jitter real | PENDIENTE (existen tramas, no tasa medida) |
| 10.000 Sa/s | Señales conocidas, preset 3, 64 pares | 100 µs nominal, medición y presencia/ausencia de `0x17` | PENDIENTE / INCIDENCIA REGISTRADA |
| Desfase CH1/CH2 | Referencia común o dos canales sincronizados | Desfase temporal entre las conversiones secuenciales | PENDIENTE |
| SPI durante 100 ventanas | Sin otro maestro simultáneo, placa estable y autorizada | Tiempo total, p50/p95/máximo, secuencia, rechazos, pérdidas | PENDIENTE |
| HTTP desde Milk-V | Servidor Apache/Nginx instalado y operativo | URL/red, código HTTP, dos curvas visibles, intervalo de refresco 1–4 s | PENDIENTE |

Las tasas nominales provienen de `period_us = 1000000 / rate_hz`, no de una medición experimental. Registrar el error relativo `100 × (f_medida - f_objetivo) / f_objetivo` y el método instrumental. No establecer una tolerancia retroactivamente.

## 6. Registro reusable de nueva evidencia

Copiar esta ficha después de **cada prueba nueva**:

```text
ID de prueba: F-____
Requisito(s): RV-____ / RD-____
Responsable(s): [por completar]
Fecha/hora/zona: [por completar]
Commit firmware / backend / frontend: [por completar]
Placa, Linux, cableado, instrumento y calibración: [por completar]
Comando o procedimiento exacto: [por completar]
Condiciones: preset, duración, carga, generador, voltaje: [por completar]
Objetivo y tolerancia previamente aprobados: [por completar]
Datos brutos, n, media, jitter, errores y unidades: [por completar]
Evidencia: tests/evidence/... o enlace verificable: [por completar]
Resultado: PASS / FAIL / BLOCKED / NOT_RUN
Conclusión limitada a lo observado: [por completar]
Revisado por / fecha: [por completar]
```

## 7. Referencias de código por criterio

La matriz completa con 38 criterios y estados diferenciados está en [MATRIZ_VERIFICACION.md](MATRIZ_VERIFICACION.md). La versión CSV equivalente está en [`tests/results/trazabilidad_requisitos.csv`](../tests/results/trazabilidad_requisitos.csv).

| Requisito(s) | Implementación / evidencia localizada | Demostración que falta |
|---|---|---|
| RV-02/03/04 | `spi_polling/main.c`: lecturas ADC y serializador | Entradas conocidas y tasas físicas en tres modos |
| RV-05/06/07/08 | `rate_hz()` y TIM2, incidencia `0x17` | Medición temporal a 100/1000/10000 Sa/s |
| RV-09 | SPI primer byte MOSI y `prepare_frame()` posterior | Preset aplicado **y** tasa medida |
| RV-10/13 | `milkv_stream.capture()`, tres transferencias físicas | SCLK, estabilidad y repetibilidad |
| RV-14/15/16 | `pc_dashboard_uart.py`, `dashboard.html` | Apache/Nginx en Milk-V y refresco visual medido |
| RV-19/20 | tests offline y dashboard vía PC | Pruebas completas MCU/SBC e integración final |
| RV-24 | **Sin archivo de video identificado en `main`** | Video Drive con todas las tasas y el montaje |

## 8. Video de demostracion y evidencia en Google Drive
https://drive.google.com/drive/folders/1vyMeNPnM6CrxiDLAD2U4zudmMIFRan2V?usp=drive_link

