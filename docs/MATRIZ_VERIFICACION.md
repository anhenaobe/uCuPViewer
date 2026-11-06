# Matriz de verificación y estado de implementación — uCuPViewer


> **Actualización de auditoría GitHub (2026-11-05, hora de Colombia):** se contrastó el contenido de este paquete con `main` en [`af58fc557934`](https://github.com/anhenaobe/uCuPViewer/commit/af58fc55793495d0e4d527ebfa83273e8443e33f). Las referencias al commit `41601d45f7` permanecen deliberadamente como **fuentes históricas exactas** de los ensayos ya documentados. Entre ambas revisiones se incorporaron `reference/prueba_1` a `reference/prueba_6`; son variantes, propuestas o paquetes de pruebas y **NO** permiten cambiar estados a PASS sin un registro experimental trazable. Véase [AUDITORIA_CAMBIOS_GITHUB.md](AUDITORIA_CAMBIOS_GITHUB.md).

**Revisión documental:** 2026-11-05  · **Base de código:** `main` en commit [`41601d45f7`](https://github.com/anhenaobe/uCuPViewer/commit/41601d45f71fb994444670fc85fe28a7be1d0a50).

Esta matriz diferencia explícitamente **qué está programado** de **qué fue probado**. Se conserva la numeración de 27 requisitos `RV-*` y 11 controles internos `RD-*` del kit anterior (se reserva `RD-02` como código histórico). No se ha ejecutado ninguna prueba nueva al generar este paquete: los resultados se derivan de evidencia ya registrada en GitHub. La columna «prueba realizada» no implica que el requisito esté completamente satisfecho.

## Convenciones de lectura

- **Código**: `SI` = existe implementación concreta (no prueba de funcionamiento); `PARCIAL` = implementación incompleta o histórica; `NO` = falta implementación de software/configuración; `NA` = criterio documental/organizativo que no se resuelve escribiendo código; `ND` = no determinado.
- **Prueba realizada**: `SI` = existe registro de al menos una prueba del aspecto; `PARCIAL` = revisión, ejecución limitada o prueba indirecta; `NO` = no hay prueba localizada en los archivos revisados. `SI` **no significa que todas las condiciones pasaron**.
- **Resultado / alcance**: `CUMPLE_ACOTADO` = evidencia positiva solo en las condiciones citadas; `PARCIAL` = evidencia incompleta; `INCIDENCIA` = fallo observado, sin generalizarlo a todas las condiciones; `PENDIENTE` = no puede dictaminarse cumplimiento integral.
- La **aceptación final** requiere criterio de medición, fecha, responsable, commit, datos brutos y evidencia accesible. Los criterios sin tolerancia numérica deben acordarla antes de ensayarse.
- `100 / 1000 / 10000 Sa/s` se interpreta **por canal** como decisión conservadora de diseño; confirmar interpretación con docente. Cada ventana contiene **64 pares CH1/CH2**, no 64 muestras totales.

## Requisitos del sistema (captura, comunicación, web)

| ID | Criterio | Código | Prueba realizada | Resultado / alcance | Evidencia / prueba |
|---|---|:---:|:---:|---|---|
| `RV-01` | Sistema Milk-V Duo S + STM32L432KC | **SI** | **SI** | PARCIAL | `F-IN01` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |
| `RV-02` | Dos señales analógicas diferenciadas | **SI** | **PARCIAL** | PARCIAL | `F-AD01` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |
| `RV-03` | Captura y almacenamiento de ventanas | **SI** | **SI** | CUMPLE_ACOTADO | `F-AD02` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |
| `RV-04` | Al menos 64 muestras por canal | **SI** | **SI** | CUMPLE_ACOTADO | `F-AD02` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |
| `RV-05` | 100 Sa/s por canal | **SI** | **NO** | PENDIENTE | `F-AD03` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |
| `RV-06` | 1000 Sa/s por canal | **SI** | **PARCIAL** | PARCIAL | `F-AD03` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |
| `RV-07` | 10000 Sa/s por canal | **SI** | **SI** | INCIDENCIA | `F-AD03; F-AD04` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |
| `RV-08` | Frecuencia de muestreo constante | **PARCIAL** | **PARCIAL** | PENDIENTE | `F-AD04` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |
| `RV-09` | Selección de preset mediante SPI | **SI** | **SI** | PARCIAL | `F-SP04` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |
| `RV-10` | Enlace SBC-MCU por SPI | **SI** | **SI** | CUMPLE_ACOTADO | `F-SP01` · [milkv_validacion_post_systick.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_validacion_post_systick.md) |
| `RV-11` | Límite teórico SPI plataforma SBC | **NA** | **NO** | PENDIENTE | `D-SPI01` · [spi_software.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/protocol/spi_software.md) |
| `RV-12` | Límite teórico SPI STM32 | **NA** | **NO** | PENDIENTE | `D-SPI01` · [README.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/README.md) |
| `RV-13` | Velocidad SPI experimental | **PARCIAL** | **PARCIAL** | PARCIAL | `F-SP03` · [milkv_validacion_post_systick.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_validacion_post_systick.md) |
| `RV-14` | Dashboard HTTP servido por SBC | **PARCIAL** | **PARCIAL** | PENDIENTE | `F-WEB01` · [pc_dashboard_uart.py](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/backend/milkv_uart/pc_dashboard_uart.py) |
| `RV-15` | Apache o Nginx en SBC | **NO** | **NO** | PENDIENTE | `D-WEB01; F-SYS01` · [nginx_ucupviewer.conf](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/infrastructure/nginx_ucupviewer.conf) |
| `RV-16` | Refresco gráfico cada 1–4 s | **PARCIAL** | **NO** | PENDIENTE | `F-WEB02` · [milkv_stream.py](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/backend/milkv_uart/milkv_stream.py) |

## Requisitos de proceso y entrega

| ID | Criterio | Código | Prueba realizada | Resultado / alcance | Evidencia / prueba |
|---|---|:---:|:---:|---|---|
| `RV-17` | Equipo de máximo seis integrantes | **NA** | **PARCIAL** | PENDIENTE | `D-DOC01` · [02_roles_responsabilidades.txt](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/02_roles_responsabilidades.txt) |
| `RV-18` | Roles y coordinación documentados | **NA** | **PARCIAL** | PARCIAL | `D-DOC01` · [02_roles_responsabilidades.txt](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/02_roles_responsabilidades.txt) |
| `RV-19` | Pruebas unitarias SBC y MCU | **PARCIAL** | **SI** | PARCIAL | `D-TEST01` · [test_protocol_offline.py](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/tests/milkv_uart/test_protocol_offline.py) |
| `RV-20` | Integración completa sistema | **PARCIAL** | **PARCIAL** | PARCIAL | `F-IN01` · [milkv_dashboard_uart_validacion.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_dashboard_uart_validacion.md) |
| `RV-21` | Repositorio reproducible | **NA** | **PARCIAL** | PENDIENTE | `D-DOC02` · [README.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/README.md) |
| `RV-22` | Descripción, arquitectura y diagramas | **NA** | **PARCIAL** | PENDIENTE | `D-DOC02` · [estado_actual.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/architecture/estado_actual.md) |
| `RV-23` | Requisitos, restricciones y verificación | **NA** | **NO** | PENDIENTE | `D-DOC02` · [05_matriz_verificacion_inicial.txt](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/05_matriz_verificacion_inicial.txt) |
| `RV-24` | Video demostrativo | **NA** | **NO** | PENDIENTE | `D-DOC03` · [video pendiente](VERIFICACION_CODIGO_Y_EVIDENCIAS.md#8-video-de-demostracion-y-evidencia-en-google-drive) |
| `RV-25` | Declaración de aportes individuales | **NA** | **NO** | PENDIENTE | `D-DOC01` · [guías del equipo](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/02_roles_responsabilidades.txt) |
| `RV-26` | Declaración de uso de IA | **NA** | **NO** | PENDIENTE | `D-DOC01` · [07_aportes_ia.txt](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/07_aportes_ia.txt) |
| `RV-27` | Bonificación >=40000 Sa/s | **NO** | **NO** | PENDIENTE | `F-AD06` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |

## Controles técnicos internos

| ID | Criterio | Código | Prueba realizada | Resultado / alcance | Evidencia / prueba |
|---|---|:---:|:---:|---|---|
| `RD-01` | Plataformas vigentes coherentes | **NA** | **PARCIAL** | PARCIAL | `D-DOC02` · [README.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/README.md) |
| `RD-03` | Contrato SC264 documentado | **SI** | **SI** | PARCIAL | `D-SP02` · [frame_sc.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/protocol/frame_sc.md) |
| `RD-04` | CRC, longitud, estado y orden | **SI** | **SI** | PARCIAL | `F-SP02` · [milkv_stream.py](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/backend/milkv_uart/milkv_stream.py) |
| `RD-05` | Niveles y protección eléctrica | **NA** | **PARCIAL** | PENDIENTE | `F-HW01` · [milkv_spi_diagnostico.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_spi_diagnostico.md) |
| `RD-06` | Desfase entre canales | **SI** | **NO** | PENDIENTE | `F-AD05` · [main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) |
| `RD-07` | Estados y datos reales distinguibles | **SI** | **PARCIAL** | PARCIAL | `F-WEB03` · [pc_dashboard_uart.py](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/backend/milkv_uart/pc_dashboard_uart.py) |
| `RD-08` | Trazabilidad de versiones y resultados | **NA** | **PARCIAL** | PENDIENTE | `D-DOC02` · [milkv_validacion_post_systick.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_validacion_post_systick.md) |
| `RD-09` | SPI GPIO explicado y comprobado | **SI** | **PARCIAL** | PARCIAL | `D-SPI01; F-SP01` · [spi_software.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/protocol/spi_software.md) |
| `RD-10` | Despliegue HTTP en Duo S | **NO** | **NO** | PENDIENTE | `F-SYS01` · [install_infra.sh](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/infrastructure/install_infra.sh) |
| `RD-11` | Recuperación frente a fallos | **PARCIAL** | **SI** | PARCIAL | `F-IN02` · [milkv_dashboard_uart_validacion.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_dashboard_uart_validacion.md) |
| `RD-12` | Suficiencia de transporte SPI por GPIO | **SI** | **PARCIAL** | PENDIENTE | `F-SP03` · [milkv_validacion_post_systick.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_validacion_post_systick.md) |


## Casos de prueba vinculados

- `F-HW01`: alimentación, tierra, pinout y señales eléctricas.
- `F-AD01..06`: dos señales, integridad de ventana, tres tasas, regularidad, desfase, bonificación.
- `F-SP01..04`: intercambio SPI, integridad de SC264, rendimiento y cambio de preset.
- `F-WEB01..03`: HTTP servido desde SBC, refresco visual y estados del navegador.
- `F-IN01..02`: cadena integrada, manejo de fallos y recuperación.
- `F-SYS01`: despliegue reproducible de Apache/Nginx en Milk-V.
- `D-SPI01`, `D-SP02`, `D-WEB01`, `D-TEST01`, `D-DOC01..03`: revisión técnica/documental.

## Observaciones que impiden declarar cumplimiento final

1. La trama activa es **SC264 (264 B)**, sin ACK, READY ni CMD8. El contrato anterior de 268 B es histórico e incompatible con el firmware importado. Fuente: [frame_sc.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/protocol/frame_sc.md).
2. El firmware actual de [spi_polling/main.c](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/firmware/stm32/spi_polling/src/main.c) usa TIM2 con **ADC por polling**; `firmware/stm32/src/` es una alternativa anterior TIM2+DMA, **no** la implementación desplegada.
3. Tres transferencias físicas válidas y tiempos de 1,783/1,791 s aparecen en [milkv_validacion_post_systick.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_validacion_post_systick.md). No demuestran frecuencia de SCLK medida ni estabilidad a largo plazo.
4. El dashboard UART/HTTP tiene datos reales en **PC/VM**, no servidor definitivo en Milk-V; dos errores de JSON UART y un incidente `0x17` a 10.000 Sa/s quedaron registrados en [milkv_dashboard_uart_validacion.md](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_dashboard_uart_validacion.md).
5. El límite interno antiguo `T_SPI <= 200 ms` no es requisito académico y no se presenta como umbral vigente. `RD-12` exige medir suficiencia de la cadena real y documentar su presupuesto temporal; fijar umbrales tras revisión del equipo.
6. Servidor: una nota manuscrita menciona Flask/Python sobre Apache; los borradores admitían Nginx. Solicitar aclaración antes de aceptar `RV-15` usando Nginx.
7. Video en Drive: **[PENDIENTE DE AÑADIR EN VERIFICACION_CODIGO_Y_EVIDENCIAS.md](VERIFICACION_CODIGO_Y_EVIDENCIAS.md#8-video-de-demostracion-y-evidencia-en-google-drive)**.

## Enlaces complementarios

- [Especificación: HU, casos, requisitos y restricciones](ESPECIFICACION_MILKV_DUOS.md).
- [Evidencia de pruebas SPI, fragmentos de código y enlace de video](VERIFICACION_CODIGO_Y_EVIDENCIAS.md).
- [Procedimientos editables](PROTOCOLOS_VERIFICACION_MILKV_DUOS.md) y [PDF](PROTOCOLOS_VERIFICACION_MILKV_DUOS.pdf).
- [Registro de resultados CSV](../tests/results/registro_pruebas.csv) e [informe LaTeX](../tests/report/INFORME_VERIFICACION.tex).
