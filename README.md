# Linux 2 · uCuPViewer

Proyecto universitario: sistema híbrido de adquisición de dos señales analógicas por microcontrolador y visualización HTTP desde Raspberry Pi con comunicación SPI.

**ESTADO: planificación técnica / interfaz v0.1 propuesta / hardware y software NO integrados.** No hay resultados experimentales todavía.

## Requisitos del profesor
- Dos canales analógicos; ventanas con **al menos 64 muestras** por canal (interpretación de diseño, pendiente de confirmar).
- Frecuencias intercambiables por SPI: **100, 1.000 y 10.000 Sa/s**. Bonificación experimental para **≥40.000 Sa/s**.
- Raspberry Pi: comunicación SPI con MCU; gráficas servidas en red por **Apache o Nginx**.
- Refresco del dashboard entre **0,25 y 1 Hz** (una actualización cada 1–4 segundos).
- Estimación teórica de máximos SPI desde hojas de datos y contraste experimental.
- Repositorio, documentación, matriz de verificación y resultados, video, declaración de aportes y declaración de IA con registro de interacciones.

## Plataforma y decisión preliminar
MCU principal recomendado: **STM32L432KC**; ESP32-S3 como alternativa bajo prueba. SBC: **Raspberry Pi, modelo exacto por confirmar**. El microcontrolador debe capturar mediante reloj/periférico de hardware y almacenar una ventana; el SBC gobierna SPI y atiende la web. Las dos entradas ADC no necesariamente se adquieren simultáneamente.

## Documentos de arranque
- `docs/01_revision_esqueleto_profesor.txt`: qué existe y qué falta del ZIP.
- `docs/02_roles_responsabilidades.txt`: asignación de seis miembros y criterios de aceptación.
- `docs/03_contratos_interfaces_v0_1.txt`: acuerdos técnicos iniciales SPI, ventana, backend y frontend. **Propuesta, NO congelada**.
- `docs/04_eleccion_mcu_y_pruebas.txt`: breve documento técnico para el grupo, con fuentes.
- `docs/05_matriz_verificacion_inicial.txt`: pruebas y evidencias a recoger (todos pendientes).
- `docs/06_flujo_git.txt`: ramas, PR, revisiones y límites de autoría.
- `docs/07_aportes_ia.txt`: formatos de registro exigidos por el profesor.
- `reference/profesor/`: códigos y diagrama originales extraídos del ZIP, sin ejecutables compilados ni carpetas `.git` anidadas.

## Árbol de trabajo
- `firmware/stm32/` y `firmware/esp32s3/`: implementaciones que aún no existen.
- `hardware/`: cableado, niveles, pinout y mediciones.
- `backend/`: adquisición desde Linux por SPI, gestión de ventanas, API.
- `frontend/`: dashboard y sus pruebas.
- `infrastructure/`: configuración HTTP, despliegue y arranque del servicio.
- `tests/`: pruebas automatizadas y evidencias de laboratorio.

## Primer hito
Revisar y aprobar interfaces; pruebas de humo de ambas placas; mock de SPI y API con datos simulados; después integrar hardware. **No subir binaries, `.o`, `.d`, `target/`, secretos ni configuraciones locales de red.**

Este paquete fue generado como propuesta de organización. El código fuente en `reference/profesor/` pertenece al esqueleto suministrado por el docente; no se atribuye a los estudiantes. Ver `docs/07_aportes_ia.txt`.
