# uCuPViewer — STM32 + Milk-V

Desarrollo actual del equipo: adquisición de dos canales en STM32L432KC, comunicación
SPI por GPIO con Milk-V y visualización HTTP. Milk-V reemplaza definitivamente a
Raspberry Pi4, descartada por problemas de conexión/inicialización.

**Estado:** código actual importado y compilación/pruebas offline disponibles; no
se ha validado físicamente esta integración. El ZIP implementa polling ADC y trama
SC264. La interfaz SPI convencional de la Milk-V del montaje no está disponible;
se conserva bit-banging. Causa/alcance de la restricción pendientes de evidencia.

## Código actual
- `firmware/stm32/spi_polling/`: firmware actual del ZIP, proyecto independiente.
- `backend/milkv_uart/`: capturador Milk-V GPIO y puente UART/HTTP PC.
- `frontend/uart_dashboard/`: dashboard del desarrollo importado.
- `tests/milkv_uart/`: pruebas offline del protocolo.

El servidor HTTP importado corre en PC; servir desde el SBC continúa pendiente.
El código identifica Milk-V Duo S y menciona Debian, pero modelo físico y sistema
instalado requieren confirmación. No se usa SPI hardware Milk-V como requisito.

## Documentación vigente del desarrollo
- [Arquitectura real y procedencia](docs/architecture/estado_actual.md).
- [SPI por software](docs/protocol/spi_software.md).
- [Trama SC264](docs/protocol/frame_sc.md).
- [Estado ADC y problemas pendientes](docs/reviews/estado_firmware.md).
- [Roles](docs/02_roles_responsabilidades.txt) y [flujo Git](docs/06_flujo_git.txt).

[Contrato v0.2](docs/03_contratos_interfaces_v0_2.txt) y [decisión anterior](docs/04_eleccion_mcu_y_pruebas.txt)
son propuestas previas. SC264 es referencia actual; revisión coordinada con Andrew,
Pipe, Ferxxo y Checho pendiente, sin imponer268 B ni cambiar paquetes silenciosamente.
Se mantienen requisitos100/1000/10000 Sa/s por canal; su precisión debe medirse.

## Implementación previa y preservación
`firmware/stm32/src/` conserva ADC+TIM2+DMA y sus evidencias anteriores. No se mezcla
con main polling; resolver esa coexistencia será tarea separada. Backend/frontend
preexistentes e infraestructura de otros integrantes no se sustituyen.
`reference/profesor/` conserva código atribuido al docente sin cambios.
La [matriz histórica](docs/05_matriz_verificacion_inicial.txt) y resultados de Checho
no se reinterpretan como validación del desarrollo actual.

## Comprobaciones sin placas
```
pio run -d firmware/stm32/spi_polling -e nucleo_l432kc
python -B tests/milkv_uart/test_protocol_offline.py
```
La rama de diagnóstico añade el handler SysTick que faltaba al firmware importado.
El [diagnóstico físico](docs/debug/milkv_spi_diagnostico.md) registra el bloqueo
en la STM32 conectada y las pruebas iniciales de recepción de ceros. Con autorización
de Andrew se programó la versión corregida: [tres transferencias físicas válidas](docs/debug/milkv_validacion_post_systick.md)
con CRC y secuencias consecutivas. La imagen anterior se conserva respaldada.
Las tasas ADC y tensiones de entrada siguen pendientes de validación.

Repositorio: [anhenaobe/uCuPViewer](https://github.com/anhenaobe/uCuPViewer).
Desarrollo por ramas/PR hacia main, sin sobrescribir aportes ni alterar PASS/FAIL
sin evidencia. ZIP original intacto fuera de Git; procedencia y autoría individual
no inferida se detallan en el documento de arquitectura.
