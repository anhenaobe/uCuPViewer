# Firmware actual SC264 por GPIO y ADC polling

Código del ZIP de trabajo del equipo. Este proyecto aislado evita sobrescribir el
firmware ADC+DMA anterior en ../src. No combinar ambos main.c.

Compilar desde raíz: pio run -d firmware/stm32/spi_polling -e nucleo_l432kc.
Core6.2.0, ststm32 19.5.0, STM32CubeL4 1.18.1, GCC ARM7.2.1; versiones copiadas de la
configuración existente y comprobadas, no del ZIP. ST-LINK configurado pero no usado
en esta tarea. La compilación pasa, pero SysTick enlaza a Default_Handler: no asumir
arranque funcional ni programar sin resolver el proyecto original completo.

Arquitectura y bloqueos: docs/reviews/estado_firmware.md desde raíz.
SC y bit-banging preservados sin cambios. La placa declarada es NUCLEO-L432KC;
pinout y modelo físico del montaje requieren verificación conjunta.
