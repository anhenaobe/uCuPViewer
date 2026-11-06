# Protocolos de verificación — Milk-V Duo S + STM32L432KC


> **Actualización de auditoría GitHub (2026-11-05, hora de Colombia):** se contrastó el contenido de este paquete con `main` en [`af58fc557934`](https://github.com/anhenaobe/uCuPViewer/commit/af58fc55793495d0e4d527ebfa83273e8443e33f). Las referencias al commit `41601d45f7` permanecen deliberadamente como **fuentes históricas exactas** de los ensayos ya documentados. Entre ambas revisiones se incorporaron `reference/prueba_1` a `reference/prueba_6`; son variantes, propuestas o paquetes de pruebas y **NO** permiten cambiar estados a PASS sin un registro experimental trazable. Véase [AUDITORIA_CAMBIOS_GITHUB.md](AUDITORIA_CAMBIOS_GITHUB.md).

**Versión:** 2026-11-05 · **Referencia de código:** [`main` 41601d45f7](https://github.com/anhenaobe/uCuPViewer/commit/41601d45f71fb994444670fc85fe28a7be1d0a50) · **Estado:** plan que distingue pruebas ya documentadas de nuevas pruebas por ejecutar. Este Markdown es la fuente editable del [PDF](PROTOCOLOS_VERIFICACION_MILKV_DUOS.pdf).

## 1. Condiciones generales antes de cualquier prueba

- Coordinar con Andrew/Valeria/Juan Fernando si se conectará o programará hardware. **No grabar firmware ni reiniciar servicios sin autorización**. Evitar controlar SPI con dos maestros simultáneos.
- Identificar físicamente Milk-V Duo S y NUCLEO-L432KC, sistema operativo, firmware cargado, cableado, tierra común, alimentación y límites analógicos. La documentación histórica de instalación Raspberry Pi **no es aplicable** a Milk-V.
- Registrar SHA(s), fecha, persona, instrumento, versión de software, comandos, preset, método de medición y datos brutos. Guardar en `tests/evidence/<tipo>/` y en `tests/results/registro_pruebas.csv`.
- `NOT_RUN` no es `FAIL`; `PASS` es únicamente para la condición exacta ensayada. Distinguir prueba offline (mock/test), inspección de código, ensayo físico y visualización.
- Verificar que toda la entrada analógica se mantenga dentro de los límites del **pin concreto**. Nunca aplicar tensiones negativas o desconocidas al ADC. No afirmar que una conversión `RAW × 3.3/4095` es voltaje calibrado.

## 2. Topología de referencia

```text
Entradas A0/PA0 y A1/PA1 → STM32L432KC: ADC polling, TIM2
          ↓
Trama SC264 de 64 pares; STM32 responde como periférico SPI GPIO
          ↓ SCLK/MOSI/MISO/CS (modo 0 intencional, verificar señales)
Milk-V Duo S como maestro SPI GPIO (bit-banging; sysfs)
          ↓ UART (ruta física actualmente documentada)
Puente HTTP en PC/VM — validación parcial ya registrada
          ↓
Dashboard en navegador
```

Asignación documental del montaje: Milk-V J3 pines 19/21/23/24 = MOSI/MISO/SCLK/CS, GPIO 461/462/463/464; STM32 D11(PB5)/D12(PB4)/D13(PB3)/A3(PA4); GND común. Referencia: [diagnóstico eléctrico](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_spi_diagnostico.md). **Verificar antes de confiar en este mapa**.

## 3. Trama SC264 y semántica temporal

| Campo | Offset | Longitud | Regla |
|---|---|---:|---|
| Firma `SC` | 0..1 | 2 B | `0x53,0x43` |
| Preset aplicado a la ventana transmitida | 2 | 1 B | 1=100; 2=1000; 3=10000 Sa/s nominales |
| Estado | 3 | 1 B | 0 = trama válida; 0x17 = período perdido; otros errores ADC/TIM |
| Secuencia | 4..5 | 2 B | `uint16` little-endian |
| 64 pares CH1/CH2 | 6..261 | 256 B | CH1/CH2 `uint16` LE intercalados; RAW 0..4095 |
| CRC16 CCITT-FALSE | 262..263 | 2 B | Sobre offsets 0..261; CRC LE, init `FFFF`, poly `1021` |

**MOSI:** el byte inicial solicita el preset nuevo y los 263 restantes son cero. El firmware transmite la ventana **ya preparada** y actualiza el preset para la siguiente adquisición después de CS alto. No existe ACK independiente, READY ni CMD8/WINDOW268. No confundir con `docs/03_contratos_interfaces_v0_2.txt`, que es histórico. Referencia: [SC264](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/protocol/frame_sc.md).

## 4. Ensayos de adquisición

### F-HW01 — Montaje, alimentación, niveles y pinout

**Método:** fotografía etiquetada, revisión de J3/STM32, multímetro y analizador lógico si está disponible. Inspeccionar tierra común y ausencia de más de 3,3 V en GPIO cuando corresponda. **Registro:** tensión medida, pin, referencia del instrumento, esquema y foto. **Pendiente:** medidas eléctricas reales completas.

### F-AD01 — Dos señales analógicas distintas

Aplicar dos entradas seguras y conocidas (por ejemplo dos niveles DC distintos dentro del rango admisible). Recibir una ventana SC264. Verificar que CH1 y CH2 cambien independientemente y que se correspondan con A0/PA0 y A1/PA1. Guardar tensión inyectada, incertidumbre, RAW y foto. **No cuenta** una ventana CH1≈4095, CH2=0 sin conocer las entradas.

### F-AD02 — 64 pares y ventana íntegra

Capturar varias ventanas para cada preset obligatorio. Confirmar 264 B, 64 pares y secuencias continuas o pérdidas registradas. Guardar trama binaria/hex y decodificación. **Evidencia ya existente:** tres transferencias correctas a preset 2; no equivalen al barrido de los tres presets.

### F-AD03 — Frecuencia efectiva por canal a 100/1000/10000 Sa/s

1. Aprobar tolerancia y método con el equipo **antes** de medir.
2. Seleccionar preset 1 y luego 2 y 3; después del cambio desechar la ventana previa si aún corresponde al preset anterior.
3. Medir independientemente los instantes de adquisición, preferiblemente mediante un marcador digital instrumentado emitido en cada muestra **sin perturbar excesivamente el firmware**. Alternativa: generador de referencia y ajuste temporal con incertidumbre documentada. No usar el eje `i/rate_hz` del dashboard como medida.
4. Capturar al menos 64 marcas o parejas por preset y calcular períodos, mediana, media, mínimo, máximo y jitter; conservar datos de instrumento.
5. Reportar cada preset **por separado**: 100 → 10 ms nominal, 1000 → 1 ms, 10000 → 100 µs. Si aparece `0x17`, registrar ventana, condiciones y fallo sin ocultarlo.

**Fórmulas:** `f_media = 1 / media(Δt)` y `error_rel_% = 100 × (f_media - f_objetivo) / f_objetivo`. Si el ADC es secuencial, no suponer que la marca de software es exactamente el sample-and-hold; estimar la desviación de la instrumentación.

### F-AD04 — Regularidad temporal y períodos perdidos

Con la misma referencia, medir distribución de `Δt_i`, desviación típica, percentiles y número de flags `0x17`; comparar con la tolerancia previamente acordada. **Hecho histórico:** un `0x17` se registró a 10000 Sa/s; no está demostrada su ausencia.

### F-AD05 — Desfase CH1/CH2

Aplicar señales sincronizadas y medir retardo entre canales o caracterizar con instrumento/firmware el orden de conversiones y sobrecarga de HAL. Registrar incertidumbre; no declarar muestreo simultáneo.

### F-AD06 — Bonificación 40000 Sa/s

Solo ejecutar si existe firmware/configuración que soporte ese preset y se acuerda el ensayo. El firmware polling actual **no** ofrece preset 4; queda pendiente, no rechazado por defecto.

## 5. Ensayos SPI

### F-SP01 — Enlace físico y señales

Evidencia registrada previamente: [tres transferencias físicas válidas](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_validacion_post_systick.md) (264 B, seq 1–3, CRC correcto). Para la nueva campaña, capturar CS, MOSI, MISO y SCLK con analizador lógico; verificar orden MSB-first, polaridad/fase, lógica 3,3 V, longitud, presencia de errores y tiempo. No confundir bit-rate efectivo con frecuencia física de SCLK.

### F-SP02 — Integridad, rechazo y estados

Pruebas offline existentes:

```bash
python3 -B -m unittest discover -s tests/milkv_uart -p 'test_*.py'
```

En registro previo figuraron 12 tests `OK`; repetir en el commit final. Ensayar corrupción CRC, firma, estado ADC, rango 12 bits y tamaño. **Limitación actual:** la decodificación no verifica exhaustivamente huecos de secuencia; añadir prueba cuando se implemente si se exige.

### F-SP03 — Rendimiento y repetibilidad

Realizar 100 transferencias por preset si el equipo acuerda ese tamaño de campaña. Medir tiempo total por ventana (`T_SPI`), bytes, rendimiento bruto y útil, errores, pérdida de ventanas, p50/p95/máximo, carga del SBC y temperatura si procede. Separar captura de transmisión si es posible.

**Datos observados antes del ensayo de repetibilidad:** 1,783 s y 1,791 s con maestro C, 264 B, velocidades efectivas reportadas de 1185/1179 bit/s. No aplican por sí mismos al criterio del dashboard bajo carga. La antigua meta de 200 ms es solo propuesta de ingeniería anterior; no reinterpretarla como exigencia del profesor.

```text
T_ciclo ≈ T_adquisicion + T_espera_preparacion + T_SPI + T_backend + T_HTTP + T_render
```

Medir esta cadena para justificar refresco visual de 1–4 s sin duplicar retardo contado en paralelo.

### F-SP04 — Cambio de preset por SPI

Solicitar `P1`, `P2`, `P3` vía interfaz actual (API/puente). Registrar primero el `requested_preset` y después comprobar `measured_preset` en una ventana **posterior**; notar que el nombre de campo `measured_preset` identifica el preset reportado, **no una tasa físicamente medida**. Confirmar la nueva tasa con `F-AD03`. Se documentó recuperación de preset 3 a 2 ante `0x17`; no equivale a validación de 10000.

## 6. HTTP, dashboard y servicios

### F-WEB01 / D-WEB01 / F-SYS01 — Servidor en Milk-V

Verificar que el servidor HTTP exigido esté ejecutándose en el SBC de destino (**la nota manuscrita menciona Flask sobre Apache; validar con el docente antes de aceptar Nginx**), que el HTTP sea accesible desde otro equipo y que `/` entregue el dashboard con dos canales. Registrar host/IP de prueba, versión del servidor, kernel, init/servicio, `curl -I` y captura del navegador. El servidor Python en PC/VM ya observado es solo integración intermedia. No ejecutar el `infrastructure/install_infra.sh` heredado para Raspberry en Milk-V.

### F-WEB02 — Intervalos de refresco

Con navegador real, registrar la marca temporal de al menos 20 actualizaciones por gráfica (Network/Performance, consola o video con marcas legibles). Calcular diferencias de tiempo y comprobar 1–4 s. Distinguir frecuencia de consultas, frecuencia de *capturas nuevas* y refresco del render.

### F-WEB03 — Estados visibles

Probar datos reales, modo demo marcado, desconexión, respuesta obsoleta, preset no aplicado y errores CRC/UART. Capturar pantalla, logs y respuesta JSON; comprobar que no se dibujan datos antiguos como «captura nueva» sin aviso.

### F-IN01 / F-IN02 — Integración y fallos

Demostrar: generador → PA0/PA1 → STM32 → SC264 → Milk-V → HTTP **alojado en Milk-V** → navegador. Registrar inicio y cierre seguro, pruebas bajo carga, desconexiones controladas y recuperación. **Evidencia actual más corta:** hasta HTTP en PC/VM, con dos errores JSON UART y recuperación documentada. No inyectar fallos eléctricos ni desconectar interfaces activas sin autorización.

## 7. Evidencia y video de tres frecuencias

El documento que centraliza **fragmentos de código, resultados históricos, tabla de tasas y espacio para Google Drive** es [`VERIFICACION_CODIGO_Y_EVIDENCIAS.md`](VERIFICACION_CODIGO_Y_EVIDENCIAS.md#8-video-de-demostracion-y-evidencia-en-google-drive). El enlace a la grabación permanece explícitamente pendiente.

Para la presentación grabada demostrar **100, 1000 y 10000 Sa/s** con señales reales, al menos 64 muestras por canal, la interfaz y el montaje. El video documenta funcionamiento, pero la **tasa real** se valida con medición independiente y logs asociados en `tests/evidence/adc/` y `tests/results/registro_pruebas.csv`.

## 8. Dictamen de salida

El responsable registra `PASS`, `FAIL`, `BLOCKED` o `NOT_RUN` para cada **ensayo**, con fecha, commit, material bruto y límites. El estado agregado del **requisito** se actualiza en la matriz solo si la evidencia cubre todas sus condiciones. La aprobación final de la matriz y tolerancias corresponde al equipo/docente, no a este paquete autogenerado.
