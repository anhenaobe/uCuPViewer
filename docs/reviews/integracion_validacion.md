# Validación de integración actual — 2026-11-05

Comandos ejecutados sin placas:
- pio run -d firmware/stm32/spi_polling -e nucleo_l432kc: SUCCESS.
  Flash6880 B/262144, RAM estática496 B/65536. Sin errores de enlace.
- python -B tests/milkv_uart/test_protocol_offline.py:8 tests OK.
  CRC conocido, pares sintéticos, corrupción, firma inválida, estado error,
  RAW fuera de rango, cotejo estático de offsets C y rutas de servidor/UI.
- compile() de ambos scripts backend/milkv_uart en Python3.11 host: sintaxis OK.
  Es código interpretado, no hay toolchain nativa Milk-V en ZIP. No ejecutado en
  distribución real; compatibilidad sysfs/stty/scheduler sigue pendiente.
- arm-none-eabi-nm ELF: Default_Handler y SysTick_Handler ambos08001bf8;
  este fallo de arranque se documenta, no se corrige cambiando firmware en este PR.
- git diff --check y enlaces locales README comprobados.

No se ejecutó C empaquetador en host: los offsets originales se cotejan estáticamente,
y el receptor real Python se prueba con fixture completo derivado de ellos.
No es prueba eléctrica ni de temporización. No upload, debug, UART, GPIO ni Device Tree.
Fuentes y ZIP cotejados, salvo única adaptación declarada de ruta HTML del servidor.
