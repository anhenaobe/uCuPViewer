# Reutilización del prototipo SPI polling

Raíz P: reference/prototipos/spi_polling_zip/osc_spi_uart_pc/.
Decisiones de revisión, no autorización para integrar. Autoría/licencia pendientes;
conservar atribución de procedencia y aclarar redistribución antes de reutilizar.

| Clase | Componente y evidencia | Justificación y cambios futuros |
|---|---|---|
| A Reutilizable | main.c crc16; milkv_stream.py crc16 | CCITT-FALSE compatible; conservar vector conocido y ajustar rango de trama en llamador |
| A Reutilizable | main.c put16 | Serialización uint16 LE útil; incorporar límites de destino y offsets del contrato |
| A Reutilizable | milkv_stream.capture, extracción pares | Orden CH1/CH2 y RAW12 compatibles; extraer función pura con N/longitud explícitos |
| B Adaptable | prepare_frame, cabecera/CRC | Separar de ADC polling y construir268 B; no copiar layout SC |
| B Adaptable | capture validaciones | Preservar rechazo de CRC/error/rango; añadir longitud, secuencia y estado contractual |
| B Adaptable | preset y first_byte | Tabla de tasas útil; IDs1/2/3 incompatibles con0/1/2; comandos requieren CRC/ACK |
| B Adaptable | tx_frame estable durante transferencia | Reemplazar exclusión bloqueante por préstamo de acquisition_get_window/release_window |
| B Adaptable | códigos0x10..0x17 y SCOPE_DATA | Diagnóstico útil, distinto del contrato; mantener error ADC separado de transporte |
| B Adaptable | pc_dashboard_uart.py --demo y dashboard.html | Herramienta de diagnóstico separada; tensión3.3 V asumida, tasa nominal no medida; HTTP debe residir en SBC según requisitos |
| B Adaptable | puente UART SerialPort/install_remote | Solo utilidad de laboratorio; depende consola root,stty y Linux; no usar como despliegue final |
| C No recomendable | gpio_spi_slave_init/wait_clock/slave_transfer | Polling de niveles, monopoliza CPU, abort espera CS indefinidamente; rehacer transporte HAL por tarea aprobada |
| C No recomendable | milkv_stream.w/r/capture como reloj definitivo | sysfs y sleeps no deterministas; pinmux ausente; sustituir por interfaz Linux soportada tras validación |
| C No recomendable | read_adc/prepare_frame temporización | Software start y polling contradicen ADC temporizado+DMA existente |
| C No recomendable | reemplazar main oficial por ZIP | Pierde SysTick y API de adquisición; reasigna PB3 y elimina DMA |

No hay pruebas fuente en el ZIP; .pyc no constituye prueba verificable. Las cuatro
pruebas offline añadidas por esta auditoría son reutilizables como vectores, no como
validación eléctrica ni cobertura de handshakes.

## Dependencias y riesgos
Conservar firmware/stm32/acquisition: ventana READY estable hasta liberación,
consumidor único y buffer no sobrescrito. Futuro transporte debe diferenciar ventana
ADC completa de TX listo, registrar errores y no bloquear callbacks. Revisar
firmware/stm32/include/acquisition.h y src/acquisition.c. No cambiar esos archivos.
PB3 LED actual vs SCLK requiere acuerdo de pinout con Valeria. Andrew, Pipe y Ferxxo
deben aprobar transporte/presets/ACK con Checho para pruebas. Milk-V reemplaza la
Raspberry Pi del contrato: decisión de plataforma pendiente en documento separado.
Estado de rama Pipe no se fusiona ni importa aquí; coordinar para evitar duplicación.

## Recomendación y tareas futuras independientes
1. Obtener Prueba_SPI completo, ELF, preparar_gpio.sh y procedencia/licencia; verificar
   SysTick y pinmux realmente usados. Es la primera acción para atribuir el bloqueo.
2. Proponer por separado recuperación CS con timeout completo y estado de TX listo;
   validar mediante máquina de estados simulada antes de conectar hardware.
3. Crear vectores dorados contractuales268 B y CMD/ACK8 B; reaprovechar CRC/LE como
   utilidades, sin crear conversor SC en esta tarea.
4. Diseñar transporte definitivo como consumidor de ventanas ADC+DMA existentes;
   reservar pines y mantener propiedad hasta fin/error de transferencia.
5. Con autorización y placas conectadas, capturar CS/SCLK/MOSI/MISO, distinguir fallo
   de arranque, pérdida de cabecera, timeout y CRC. Medir adquisición por separado.
6. Revisar futura visualización/HTTP con responsables: ni el valor rate_hz ni
   measured_preset del dashboard demuestran frecuencia medida experimentalmente.

Prioridad: resolver arranque/CS/readiness antes de aumentar velocidad. Reutilizar
utilidades pequeñas y vectores; no adoptar el bucle GPIO/polling como arquitectura.
Estas tareas no se ejecutaron. El prototipo permanece referencia identificada.
