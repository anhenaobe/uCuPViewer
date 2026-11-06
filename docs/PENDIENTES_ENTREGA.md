# Estado de entrega y pendientes — uCuPViewer


> **Actualización de auditoría GitHub (2026-11-05, hora de Colombia):** se contrastó el contenido de este paquete con `main` en [`af58fc557934`](https://github.com/anhenaobe/uCuPViewer/commit/af58fc55793495d0e4d527ebfa83273e8443e33f). Las referencias al commit `41601d45f7` permanecen deliberadamente como **fuentes históricas exactas** de los ensayos ya documentados. Entre ambas revisiones se incorporaron `reference/prueba_1` a `reference/prueba_6`; son variantes, propuestas o paquetes de pruebas y **NO** permiten cambiar estados a PASS sin un registro experimental trazable. Véase [AUDITORIA_CAMBIOS_GITHUB.md](AUDITORIA_CAMBIOS_GITHUB.md).

**Revisión:** 2026-11-05 · **`main` consultada:** [`41601d45f7`](https://github.com/anhenaobe/uCuPViewer/commit/41601d45f71fb994444670fc85fe28a7be1d0a50). Este archivo sustituye el diagnóstico anterior basado en el ZIP antiguo; los resultados no han sido repetidos aquí.

## Evidencia de progreso ya documentada

- Firmware actual `firmware/stm32/spi_polling/` con ADC por polling, TIM2 y trama SC264; corrección SysTick versionada y programada con autorización.
- **Tres transferencias físicas SPI válidas** (264 B, CRC, seq 1/2/3) en [validación física](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_validacion_post_systick.md).
- **12 pruebas offline** reportadas `OK` en [validación UART/HTTP](https://github.com/anhenaobe/uCuPViewer/blob/41601d45f71fb994444670fc85fe28a7be1d0a50/docs/debug/milkv_dashboard_uart_validacion.md) y fuente de tests en `tests/milkv_uart/`. No se reejecutaron en la creación de estos documentos.
- Ruta **STM32 → SPI GPIO → Milk-V → UART → puente HTTP PC/VM** con `source=hardware`, 64 muestras y secuencias crecientes; **NO** demuestra HTTP alojado en el SBC ni render final.
- Registro de **dos errores JSON UART** en 37 capturas válidas de una sesión y de `0x17` a preset 3 (10000 Sa/s nominales); se conserva la recuperación a preset 2.

## Pendientes de máxima prioridad para cumplir el enunciado

- [ ] Medir la tasa **real** de 100 Sa/s con 64 pares/ventana, instrumento y registros brutos.
- [ ] Medir la tasa **real** de 1000 Sa/s; distinguir preset nominal y período efectivo.
- [ ] Investigar y resolver o delimitar `0x17` a 10000 Sa/s; medir frecuencia y estabilidad bajo condiciones conocidas.
- [ ] Validar dos entradas analógicas con fuentes conocidas y documentar rango seguro, pinout, GND y posible desfase CH1/CH2.
- [ ] Registrar SCLK físico, CPOL/CPHA, CS, voltajes e integridad SPI con instrumento; ejecutar campaña de repetibilidad bajo carga.
- [ ] Implementar/validar servicio web **desde Milk-V Duo S** con Apache/Nginx, sin instalar scripts para Raspberry.
- [ ] Medir refresco de ambas gráficas entre 1 y 4 s con navegador real y señal física.
- [ ] Documentar errores de UART, reinicio, recuperación y política de datos obsoletos.
- [ ] Completar material de reproducción: instalación real, diagrama/pinout, fuente del programa instalado en Milk-V y versiones.
- [ ] Obtener y revisar **video en Drive** con 100/1000/10000 Sa/s; añadir URL y marcas de tiempo en `VERIFICACION_CODIGO_Y_EVIDENCIAS.md`.
- [ ] Obtener aportes individuales/IA verificados, enlaces PR/commits y revisión de responsables.

## Diferencias de rama no fusionadas

Al corte, los PR [#3](https://github.com/anhenaobe/uCuPViewer/pull/3), [#4](https://github.com/anhenaobe/uCuPViewer/pull/4) y [#7](https://github.com/anhenaobe/uCuPViewer/pull/7) estaban **abiertos**. Pueden contener contratos y pruebas nuevas; **no** atribuirlos automáticamente a `main` ni dar por finalizada su integración. Revisar otra vez antes del PR de QA.

## Priorización de esta rama

1. Asegurar consistencia entre especificación, matriz y SC264.
2. Centralizar rutas de implementación y resultados parciales existentes.
3. Recibir mediciones y registrar resultados reales, incluidos fallos.
4. Incorporar URL del video y validar los tres modos antes de marcar `RV-24` como completado.
5. Solicitar revisión de Andrew, Valeria, Felipe, Juan Fernando y Mateo según el subsistema afectado.

**No hacer desde `verificationmatrix`:** reemplazar firmware actual, reprogramar placas, ejecutar instaladores de Raspberry sobre Milk-V, eliminar evidencia negativa o mezclar los dos proyectos STM32 sin revisión.
