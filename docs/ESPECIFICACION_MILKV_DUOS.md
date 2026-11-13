# Especificación de requisitos, casos de uso y restricciones — uCuPViewer


> **Actualización de auditoría GitHub (2026-11-05, hora de Colombia):** se contrastó el contenido de este paquete con `main` en [`af58fc557934`](https://github.com/anhenaobe/uCuPViewer/commit/af58fc55793495d0e4d527ebfa83273e8443e33f). Las referencias al commit `41601d45f7` permanecen deliberadamente como **fuentes históricas exactas** de los ensayos ya documentados. Entre ambas revisiones se incorporaron `reference/prueba_1` a `reference/prueba_6`; son variantes, propuestas o paquetes de pruebas y **NO** permiten cambiar estados a PASS sin un registro experimental trazable. Véase [AUDITORIA_CAMBIOS_GITHUB.md](AUDITORIA_CAMBIOS_GITHUB.md).

**Base revisada:** `main` [`41601d45f7`](https://github.com/anhenaobe/uCuPViewer/commit/41601d45f71fb994444670fc85fe28a7be1d0a50) · **Fecha de corte:** 2026-11-05 · **Estado:** documento de QA propuesto para revisión del equipo, no contrato congelado.

## 1. Necesidad y objetivo

Implementar un osciloscopio didáctico híbrido que permita captar dos señales analógicas con una STM32L432KC, transferir ventanas por SPI a la Milk-V Duo S, y presentar ambas formas de onda en un navegador mediante un servidor HTTP alojado en el SBC. El sistema permite estudiar periféricos, temporización, interoperabilidad, rendimiento SPI y verificación reproducible.

**Alcance académico adoptado (ver aclaración de servidor más abajo):** dos entradas analógicas; 64 muestras como mínimo (se adoptan **64 por canal**); muestreo seleccionable a 100, 1.000 y 10.000 muestras/segundo (se adoptan **tasas por canal**); control por SPI; estimación teórica y medición experimental del enlace; dashboard HTTP con Apache o Nginx alojado en el SBC y actualización entre 1 y 4 s; pruebas, documentos, aportes y video. Bonificación opcional: 40.000 Sa/s. Estas interpretaciones deben contrastarse con el enunciado definitivo si el equipo dispone de él.

**Aclaración documental del servidor:** la nota de clase manuscrita facilitada por el equipo menciona «Flask en Python y montado en Apache», mientras los borradores de especificación y matriz anteriores admitían «Apache o Nginx». **No se resuelve aquí esa diferencia:** antes de aprobar `RV-15`, confirmar con el docente si Apache/Flask es obligatorio o Nginx está permitido. En cualquier caso, el servicio debe comprobarse alojado en el SBC y no solo en PC.

## 2. Historias de usuario

| ID | Historia | Valor |
|---|---|---|
| HU-01 | Como operador, quiero ver simultáneamente CH1 y CH2 desde un navegador. | Comparación de formas de onda. |
| HU-02 | Como operador, quiero elegir entre 100, 1000 y 10000 Sa/s. | Ajustar resolución temporal. |
| HU-03 | Como operador, quiero distinguir datos reales, simulados, antiguos y erróneos. | Evitar interpretación falsa. |
| HU-04 | Como desarrollador, quiero un formato SPI único y documentado. | Interoperabilidad entre STM32 y Milk-V. |
| HU-05 | Como responsable QA, quiero vincular requisitos con código, pruebas y evidencias. | Trazabilidad auditable. |
| HU-06 | Como evaluador, quiero reproducir el montaje y revisar video y resultados. | Comprobación independiente. |

## 3. Casos de uso

| ID | Actor | Flujo correcto | Alternativa / límite | Matriz |
|---|---|---|---|---|
| CU-01 | Operador | Abre dashboard HTTP y visualiza CH1/CH2. | Si no hay datos válidos, se muestra el error; no se inventan curvas reales. | RV-02, RV-14, RD-07 |
| CU-02 | Operador | Cambia preset en UI; el puente envía `P1/P2/P3`, Milk-V manda código en **primer byte MOSI**, STM32 aplica el nuevo valor a la **captura siguiente**. | El HTTP 200 de `/api/preset` solo confirma recepción del pedido por el puente, **no** tasa física aplicada. Confirmar `measured_preset` y medir frecuencia aparte. | RV-05..09 |
| CU-03 | Sistema | STM32 prepara 64 pares CH1/CH2; se transmite una ventana **SC264** y el receptor valida longitud, firma, CRC y rango. | Trama con error se rechaza; no hay comando READY ni ACK en SC264. | RV-03/04/10, RD-03/04 |
| CU-04 | Operador | Revisa actualizaciones de gráficas cada 1–4 s. | Mostrar antigüedad y pérdida de comunicación; medir cadencia visual real. | RV-16, RD-07 |
| CU-05 | QA | Documenta evidencia: ruta de código, procedimiento, fecha, versión, datos brutos, video y dictamen. | Un ensayo parcial no acredita todo el requisito. | RV-19..26, RD-08 |

## 4. Requisitos verificables

**Leyenda:** `E` = exigencia académica de acuerdo con las notas del proyecto; `D` = decisión interna de diseño/verificación. La columna de estado se mantiene en [la matriz](MATRIZ_VERIFICACION.md), no aquí.

| ID | Origen | Requisito | Trazabilidad |
|---|:---:|---|---|
| RF-01 | E | Capturar dos señales analógicas distinguibles en ventanas. | RV-02/03 |
| RF-02 | E | Al menos 64 muestras; criterio conservador interno: 64 por canal. | RV-04 |
| RF-03 | E | Mantener frecuencia de muestreo constante y cuantificar desviación. | RV-08 |
| RF-04 | E | Disponer de presets 100/1000/10000 Sa/s. | RV-05/06/07 |
| RF-05 | E | Permitir selección de preset por SPI. | RV-09 |
| RF-06 | E | Transferir capturas entre STM32 y Milk-V mediante SPI. | RV-10/13 |
| RF-07 | E / confirmar | Publicar dashboard HTTP desde SBC. Nota de clase: Flask/Python sobre Apache; la variante Nginx de los borradores anteriores requiere confirmación del docente. | RV-14/15 |
| RF-08 | E | Actualizar gráficas a 0,25–1 Hz (intervalos de 1–4 s). | RV-16 |
| RNF-01 | E | Calcular cotas teóricas SPI y medir rendimiento experimental. | RV-11/12/13 |
| RNF-02 | D | Registrar CRC, secuencia y estado, rechazando tramas incorrectas. | RD-03/04 |
| RNF-03 | D | Medir si el ciclo adquisición → SPI → HTTP → pantalla cumple la cadencia. | RD-12, RV-16 |
| RNF-04 | D | Diferenciar valores RAW ADC, voltajes calculados y medidas calibradas. | RD-07 |
| RNF-05 | D | Conexiones GPIO/ADC a niveles eléctricos compatibles y documentados. | RD-05 |
| RNF-06 | D | Evidencia por commit, fecha, instrumento, configuración y responsable. | RD-08 |
| RG-01 | E | Equipo de máximo seis personas y responsabilidades declaradas. | RV-17/18/25 |
| RG-02 | E | Pruebas unitarias de MCU y SBC e integración del sistema. | RV-19/20 |
| RG-03 | E | Repositorio, arquitectura, restricciones, instalación y matriz auditables. | RV-21/22/23 |
| RG-04 | E | Video funcional de las tres tasas obligatorias. | RV-24 |
| RG-05 | E | Declarar aportes individuales y utilización de IA con evidencia. | RV-25/26 |
| BON-01 | E | Bonificación si se demuestran al menos 40000 Sa/s. | RV-27 |

## 5. Arquitectura implementada y alcance de las pruebas existentes

```text
CH1 PA0 / CH2 PA1 (ADC 12 bits, lecturas secuenciales)
                ↓
STM32L432KC: TIM2 + polling ADC → 64 pares → SC264 (CRC16)
                ↓  SPI modo 0 por GPIO: SCLK, MOSI, MISO, CS
Milk-V Duo S: bit-banging en Python o maestro C instalado
                ↓  UART / consola (camino validado)
PC/VM: puente Python → /api/state, /api/preset → HTTP
                ↓
Navegador / dashboard de dos canales
```

**Distinción indispensable:** las pruebas de la etapa actual llegan hasta el servidor HTTP **en PC/VM**, no acreditan Apache/Nginx ejecutándose en el SBC. `firmware/stm32/src/` contiene ADC+TIM2+DMA de un desarrollo anterior y no debe confundirse con `firmware/stm32/spi_polling/`.

## 6. Restricciones y acuerdos pendientes

| ID | Naturaleza | Condición |
|---|---|---|
| R-01 | Plataforma | Milk-V Duo S (SG2000) y STM32L432KC/NUCLEO-L432KC. Raspberry Pi descartada del montaje actual. |
| R-02 | Comunicación | SPI convencional no disponible en el Linux/montaje actual; usar GPIO por software. No concluir que SG2000 carece físicamente de controlador SPI. |
| R-03 | Temporización | TIM2 establece un período nominal; el ADC por polling no realiza conversión simultánea en ambos canales ni ofrece garantía metrológica sin medición. |
| R-04 | Formato activo | Trama SC264 de 264 bytes; 64 pares uint16 LE; CRC16-CCITT-FALSE. Sin CMD8/ACK8 ni READY. |
| R-05 | Presets | IDs 1/2/3 = 100/1000/10000 Sa/s nominales. Se aplican a la próxima adquisición; no se confirma tasa mediante ACK. |
| R-06 | Seguridad | Verificar GND común, pinout J3, niveles de 3,3 V y tensiones ADC con instrumento antes de conectar señales. |
| R-07 | Integración | El HTTP académico debe estar en SBC con Apache/Nginx; el puente PC es evidencia intermedia, no sustituto definitivo. |
| R-08 | Reproducibilidad | No ejecutar scripts Raspberry `infrastructure/install_infra.sh` sobre Milk-V; documentar imagen real, init, GPIO, servicios y fuentes instaladas. |
| R-09 | Calidad | Registrar pérdida de período `0x17`, errores JSON UART, variación temporal y condiciones de recuperación. |
| R-10 | Criterios abiertos | Confirmar con docente tasa por canal/global, tolerancia de exactitud/jitter y metodología de evaluación; definirlos antes del cierre. |

## 7. Referencias del propio repositorio

- [Arquitectura del desarrollo actual](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/architecture/estado_actual.md).
- [Protocolo SC264](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/protocol/frame_sc.md).
- [SPI por software](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/protocol/spi_software.md).
- [Validación física de SPI](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_validacion_post_systick.md).
- [Validación UART/HTTP e incidencia a 10 kSa/s](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_dashboard_uart_validacion.md).
- [Matriz de verificación](MATRIZ_VERIFICACION.md) y [evidencias de código/video](VERIFICACION_CODIGO_Y_EVIDENCIAS.md).

**Nota de vigencia:** la fecha de revisión identifica el commit estudiado, no certifica que todos los criterios se hayan aprobado. Las ramas con PR abiertos pueden evolucionar independientemente de `main`.
