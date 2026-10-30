# STM32 ADC + TIM2 + DMA — primer hito

Responsable: Andrew. NUCLEO-L432KC asumida; confirmar placa y pinout con Valeria.
Implementación compilada y pruebas de API ejecutadas en placa; tasas físicas no medidas. No implementa SPI.

## Construcción reproducible
Instalar PlatformIO Core 6.2.0 y ejecutar desde la raíz:
```
pio run -d firmware/stm32 -e nucleo_l432kc
pio run -d firmware/stm32 -e nucleo_l432kc -t upload
pio debug -d firmware/stm32
```
Conectar el USB ST-LINK integrado para upload/debug. Programación ST-LINK verificada y ejecución de pruebas confirmada por depurador. Dependencias efectivamente resueltas y fijadas en
platformio.ini: ststm32 19.5.0, STM32CubeL4 1.18.1 (HAL 1.13.5), GCC ARM
7.2.1/package 1.70201.0, linker scripts 0.2.0. Startup y SystemInit provienen del
framework. La aplicación define una única implementación SysTick para HAL_IncTick.

## Arquitectura y propiedad
main configura reloj y LED PB3, inicia una ventana a 1000 Sa/s y llama poll.
LED encendido significa ventana completa; el buffer queda retenido para depuración.
acquisition encapsula ADC/TIM/DMA y API. Todas las llamadas públicas se hacen desde
un único contexto principal, nunca desde ISR. Los callbacks detienen TIM2 y publican
flags; poll realiza limpieza HAL y publica READY. No hay procesamiento por muestra.
Estados ACQ_IDLE, ACQ_ACQUIRING, ACQ_READY y ACQ_ERROR. READY significa ADC completo,
no TX SPI preparado. get_window devuelve NULL hasta READY; el puntero const es
válido hasta release_window. Start, stop y cambios de preset rechazan READY.
El consumidor debe terminar antes de liberar. Stop aborta captura incompleta y
permite recuperación de error solo tras inicialización exitosa. Un fallo de init
requiere reinicio; no se permite reinit que invalide una ventana prestada.

## Relojes, ADC y DMA
HSI16, sin PLL: SYSCLK/HCLK/PCLK1/PCLK2 = 16 MHz nominales, APB divisores 1.
TIM2 = PCLK1 (doble si APB1 divide); PSC se calcula desde HAL_RCC_GetPCLK1Freq.
ADC síncrono HCLK/2 = 8 MHz. Escaneo regular de 12 bits, ranks 5 y 6, flanco
ascendente TIM2 TRGO update; continuo y discontinuo deshabilitados (estructura cero).
Calibración single-ended antes de start. Muestreo 47.5 ciclos + 12.5 conversión:
60 ciclos/canal = 7.5 us; secuencia 15 us nominales, menor que 100 us del preset
más rápido. Considerar latencia de sincronización y comprobar impedancia de fuente.
No son canales simultáneos. HSI y reloj real introducen tolerancia no medida.

fs = f_TIM2 / ((PSC+1)*(ARR+1)). Contador a 1 MHz:

| Sa/s por canal | PSC | ARR | fs nominal | error de división |
|---|---|---|---|---|
|100|15|9999|100|0%|
|1000|15|999|1000|0%|
|10000|15|99|10000|0%|

40 kSa/s se rechaza. TIM2 no genera interrupciones periódicas. La configuración
carga registros antes de armar ADC; start reinicia contador sin generar UG.
DMA1 canal1/request0, normal, halfword, incremento de memoria; solicitudes ADC
limitadas. 128 conversiones = 256 bytes, CH1[0],CH2[0],...,CH1[63],CH2[63].
La interrupción DMA detiene timer, y HAL_TIM_Base_Stop fuera de ISR restaura estado
HAL para repetir capturas. Overrun/error DMA provoca ERROR; no se expone ventana.

## Pinout provisional
PA0/A0/CN4-12 = ADC1_IN5 CH1; PA1/A1/CN4-11 = ADC1_IN6 CH2.
Son entradas expuestas; SWD PA13/PA14 y VCP PA2 quedan libres. PA1 puede ser SPI SCK
alternativo: reservar otra ruta futura. PB3 LED también puede ser SCK; deberá
liberarse si SPI usa PB3/PB4/PB5. Ninguna ruta SPI se configura en este hito.
Entradas entre VSSA y VREF+, dentro de límites de VDDA/datasheet. No conectar
señales negativas ni 5 V; medir alimentación/referencia y compartir tierra.

## Verificación
T01: build ARM y enlace ejecutados. Revisar ELF con arm-none-eabi-nm: handlers
ADC1, DMA1_Channel1 y SysTick presentes una vez; startup del framework.
T02–T05: test/target_test.c contiene pruebas ejecutables en placa: presets inválidos,
operaciones rechazadas, buffer no disponible durante captura, rango de valores,
dos capturas consecutivas por preset, liberación y aborto. Ejecutadas en placa: retorno 0, ver evidencia de hardware.
Ejecutar el entorno acquisition_test indicado abajo; requiere placa y entradas seguras. La prueba no
verifica físicamente cadencia, ni demuestra ausencia general de corrupción.
Para errores, desconectar/inyectar fallo de DMA bajo depurador, observar ERROR y
recuperación mediante stop; errores de init deben permanecer ERROR hasta reset.
T05 revisión estática: buffer alineado, assert de 256 bytes, DMA normal limitado a
128 transferencias y exclusión de start en READY. Pendiente comprobación dinámica.

T06 pendiente: aplicar dos DC distintas conocidas; verificar pares y 64 valores por
canal. Para cada preset observar PSC/ARR, NDTR 128→0, estados y estabilidad del buffer
mientras se mantiene READY; repetir sin cambiar preset. Medir señales/rampa conocida
y contrastar su muestreo. Para medir TRGO, en una tarea de instrumentación puede
sacarse un canal timer sincronizado: documentar su relación exacta con el trigger.
El LED actual marca finalización/limpieza de ventana, no cada conversión ADC.
Registrar instrumento, resolución, firmware SHA, montaje y tolerancias acordadas
con Checho. No modificar sus resultados existentes. Cadencia y tensiones conocidas pendientes; ver evidencia limitada de hardware.

## Limitaciones e integración futura
No timeout automático de captura: el cliente puede abortar mediante stop si DMA no
termina. ERROR actualmente identifica fallo genérico; diagnóstico detallado se consulta
en handles HAL con debugger. No streaming ni doble buffer. Futuro SPI debe respetar
la propiedad de la ventana, separar READY ADC de TX y acordar pines y tiempos.
La documentación compartida aún describe firmware no creado; proponer su actualización
por separado al revisar este hito, sin modificarla aquí.

## Referencias
- RM0394: https://www.st.com/resource/en/reference_manual/rm0394-stm32l41xxx42xxx43xxx44xxx45xxx46xxx-advanced-armbased-32bit-mcus-stmicroelectronics.pdf
- Datasheet: https://www.st.com/resource/en/datasheet/stm32l432kc.pdf
- UM1956: https://www.st.com/resource/en/user_manual/um1956-stm32-nucleo32-boards-mb1180-stmicroelectronics.pdf
- Ejemplo ST: https://github.com/STMicroelectronics/STM32CubeL4/tree/master/Projects/NUCLEO-L432KC/Examples/ADC/ADC_DMA_Transfer
- HAL/LL instalados: stm32l4xx_hal_adc.h (trigger y DMA), stm32l4xx_ll_adc.h,
  stm32l4xx_hal_tim.c (start/stop), stm32l4xx_hal_adc.c (callbacks).

Entorno de pruebas listo: pio run -d firmware/stm32 -e acquisition_test -t upload.
Consultar acquisition_test_result en debugger: -1 no terminado, 0 éxito, otra cifra
línea fallida. Ese entorno incluye automáticamente test/target_test.c.
Build normal final: Flash 8376 B, RAM estática 568 B.
