# Estado del firmware STM32 actual

Actualización de diagnóstico: se añadió el handler SysTick en un archivo separado.
Las observaciones de importación siguientes describen el estado anterior a esa
corrección. Ver [evidencia física y validación actual](../debug/milkv_spi_diagnostico.md)
para distinguir el firmware instalado del proyecto local corregido.

El ZIP contiene trabajo actual del equipo, no código externo descartable. Se
integra sin cambios en firmware/stm32/spi_polling/src/main.c. Su proyecto PlatformIO
independiente evita sobrescribir firmware/stm32/src/acquisition.c y main.c previos.
La configuración se deriva de versiones instaladas y previamente usadas, no del
ZIP (que no incluye platformio.ini). No se fusionan las dos implementaciones.

## Adquisición actual
adc_init_safe configura ADC1 a12 bits, HCLK/2=8 MHz nominal, sin scan, software start,
una conversión cada vez y sin DMA. PA0/A0 IN5 y PA1/A1 IN6 son los canales.
read_adc cambia rank1, inicia, polls conversión hasta5 ms, lee y detiene. Muestreo
47.5 ciclos. prepare_frame usa TIM2 PSC15 con HSI16 y polls UIF: ARR9999/999/99 para
100/1000/10000 nominales. No es disparo ADC por timer: CPU inicia ambas conversiones
tras observar UIF. Dos lecturas secuenciales, con overhead HAL y jitter software.
Buffers: tx_frame[264],64 pares LE en6..261; una ventana estable durante transmisión,
siguiente captura después de CS alto. Bloquea escucha SPI mientras captura.
Código detecta periodo perdido con UIF después del par (0x17) y timeout timer0x16;
error init/calibración/config/start/poll se marca0x10..0x15. Tick debe funcionar.
No hay medidas que demuestren tasas obligatorias; polling podría satisfacerlas si
latencia y conversiones caben y jitter cumple tolerancia acordada. A10k solo hay
100 us por par y se requiere medición. No sustituirlo por DMA en este PR.

## Problemas antes de continuar
- main.c:285 HAL_Init habilita tick pero archivo no define SysTick_Handler.
  Build con solo fuentes aportadas enlaza SysTick al Default_Handler, ambos08001bf8.
  Puede bloquearse al primer tick antes de SPI. Prueba_SPI externo podría aportar
  handler: pedir proyecto/ELF realmente cargado. No se afirma causa física probada.
- slave_transfer:272/278 espera CS alto sin límite incluso al abortar tras timeout.
- prepare_frame y milkv_stream.capture no garantizan TX listo; ver spi_software.md.
- Firmware ADC anterior usa PB3 como salida LED: no combinar su init con SCLK PB3.
- Preparación GPIO de Milk-V y proyecto original completo no incluidos.

## Qué aprovechar
crc16/put16 y distribución intercalada, validaciones de firma/CRC/RAW y errores,
retención de buffer durante transmisión, puente UART y dashboard actuales son
componentes útiles. Conservarlos, no imponerles formato268 B. Bit-banging es una
necesidad del montaje actual, por lo que requiere mejorar timeouts/readiness y
medirlo, no descartarlo por comparación con otra arquitectura.
Requieren revisión: waits bloqueantes, dependencia SysTick, señalización de error,
control de secuencia, temporización ADC y mensajes que puedan confundir tasa
configurada con medida (pc_dashboard_uart.handle_data usa rate del código preset).

## Validación y próximos hitos acotados
Compilación aislada previa: SUCCESS6880 B Flash/496 B RAM. Repetir con
pio run -d firmware/stm32/spi_polling -e nucleo_l432kc. Build no implica ejecución.
Pruebas offline CRC/parser en tests/milkv_uart: no interactúan con placas.
No se prueba UART,GPIO ni programación aquí. Evidencias históricas DMA se preservan
sin atribuir sus resultados al polling actual.

1. Confirmar ISR del proyecto cargado y corregir arranque en PR pequeño posterior.
2. Recuperación CS acotada y TX-ready compatible con ambos GPIO, con pruebas simuladas.
3. Obtener script pinmux y documentar restricción del montaje Milk-V sin recuperar SPI hardware.
4. Medir presets con entradas conocidas y trazas, previa autorización/conexión.
5. Evaluar TIM→ADC→DMA como mejora independiente si polling no satisface tolerancia;
   preserva interfaz de ventana, exige aprobación y no modifica SC por sí mismo.
6. Revisar contrato/plataforma y servicio HTTP conjuntamente con Andrew/Pipe/Ferxxo/Checho.
