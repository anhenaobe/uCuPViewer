# Firmware actual SC264 por GPIO y ADC polling

Código del ZIP de trabajo del equipo. Este proyecto aislado evita sobrescribir el
firmware ADC+DMA anterior en ../src. No combinar ambos main.c.

Compilar desde raíz: pio run -d firmware/stm32/spi_polling -e nucleo_l432kc.
Core6.2.0, ststm32 19.5.0, STM32CubeL4 1.18.1, GCC ARM7.2.1; versiones copiadas de la
configuración existente y comprobadas, no del ZIP.

Corrección de arranque: `src/stm32l4xx_it.c` define SysTick_Handler y actualiza el
tick HAL. La importación original enlazaba ese vector al bucle Default_Handler.
El diagnóstico físico y el estado de programación se registran en
[docs/debug/milkv_spi_diagnostico.md](../../../docs/debug/milkv_spi_diagnostico.md).
No asumir que este proyecto coincide con el binario instalado ni programarlo sin
resolver esa correspondencia. ADC polling y SPI GPIO conservan su implementación.

Arquitectura y bloqueos: docs/reviews/estado_firmware.md desde raíz.
SC y bit-banging preservados sin cambios. La placa declarada es NUCLEO-L432KC;
pinout y modelo físico del montaje requieren verificación conjunta.
