# Prototipo SPI polling conservado para auditoría

NO constituye el firmware integrado de uCuPViewer. No seguir automáticamente las
instrucciones de reemplazo/programación del README original.

Procedencia: ZIP osciloscopio_uart_sin_ethernet.zip aportado por Andrew para revisión
el 2026-11-05. Esto no acredita autoría. Autor y licencia del contenido no constan;
permiso de redistribución general no verificado. La importación al repositorio fue
solicitada expresamente; aclarar licencia antes de reutilización/distribución externa.
SHA256 original: 26084F7C02791D1B1908BE035845C370718E375F20AF2A5DD56DF53DF94E7059.
El ZIP se conserva fuera de Git, intacto. Fuentes importadas byte a byte.

Plataformas declaradas: NUCLEO-L432KC, Milk-V Duo S y PC Debian. C con STM32Cube HAL;
Python 3 estándar, sysfs GPIO, consola UART y stty; HTML/JavaScript en navegador.

Inventario conservado bajo osc_spi_uart_pc/:
- README.md: instrucciones originales, con dependencias externas no incluidas.
- stm32/src/main.c: ADC polling y periférico SPI GPIO.
- pc/milkv_stream.py: controlador GPIO ejecutado en Milk-V.
- pc/pc_dashboard_uart.py: cargador UART y servidor HTTP en PC.
- pc/dashboard.html: visualización.
Excluidos los dos .pyc y __pycache__ del ZIP. No incluye platformio.ini ni
preparar_gpio.sh; dependen del proyecto externo Prueba_SPI y configuración de Milk-V.

Compilación aislada del main.c SIN modificarlo usando configuración del firmware
actual: ststm32 19.5.0, STM32CubeL4 1.18.1, GCC7.2.1, Core6.2.0: SUCCESS,
6880 B Flash, 496 B RAM estática. No prueba reproducibilidad del proyecto externo.
SysTick enlaza al Default_Handler: la compilación no acredita ejecución correcta.

Diferencias: SC de 264 B, presets1/2/3, SPI GPIO en ambos extremos, captura por
polling y HTTP en PC. Firmware oficial conserva ADC+TIM2+DMA; contrato v0.2 es una
propuesta distinta de 268 B. Ver docs/reviews/prototipo_spi_polling_auditoria.md y
prototipo_spi_polling_reutilizacion.md desde la raíz del repositorio.
