DEMO OSCILOSCOPIO: MILK-V DUO S + NUCLEO-L432KC

ESTADO: PROTOTIPO PARA VALIDACIÓN. No sustituye adquisición Timer TRGO + ADC DMA,
ni garantiza refresco de 0.25 a 1 Hz. Requiere medir tiempos y verificar sincronización SPI.

1. STM32 (PC con PlatformIO)
   Copiar stm32/platformio.ini y stm32/src/main.c a tu proyecto.
   Cargar con pio run -t upload.

2. Conexión con placas apagadas:
   Milk-V B13/J3-19 MOSI -> STM D11/PB5
   Milk-V B14/J3-21 MISO <- STM D12/PB4
   Milk-V B15/J3-23 SCLK -> STM D13/PB3
   Milk-V B16/J3-24 CS   -> STM A3/PA4 (NSS hardware)
   Milk-V J3-25 GND      -> STM GND
   Alimentaciones USB independientes; compartir GND. Todos los pines a 3.3V.
   ADC CH1 STM A0/PA0; ADC CH2 STM A1/PA1.
   NO conectar señales desconocidas, de >3.3V o negativas.

3. MILK-V:
   Preparar GPIO mediante ./preparar_gpio.sh (creado anteriormente), comprobando errores.
   Copiar milkv/osc_spi.py a /root/osciloscopio/spi/osc_spi.py
   python3 osc_spi.py 2
   (No funciona con el antiguo firmware de cuatro bytes: el nuevo firmware
   responde 260 bytes con cabecera SC.)

4. PROTOCOLO:
   SPI modo 0. Una transacción de 260 bytes.
   Maestro manda primer byte preset 1,2,3 y rellena 259 bytes 0.
   STM responde 'S','C', preset ACTUAL, secuencia (1 byte), 64 parejas ADC de 16 bit LE.
   Al completar la transferencia STM aplica preset y captura la SIGUIENTE ventana.
   La primera respuesta corresponde al preset inicial 1000 Sa/s.
   Espera >1s entre transferencias.

5. LIMITACIONES:
   Captura temporizada con bandera de actualización TIM2 y conversiones ADC por
   software: NO cumple todavía garantía estricta de sampling uniforme. A 10 kSa/s
   necesita verificación en osciloscopio; migrar a TIM TRGO+ADC+DMA en versión final.
   Comunicación bit-banging de Python sysfs puede tardar más de 4 segundos.
   Por tanto NO afirmar todavía cumplimiento del dashboard 0.25–1 Hz.
