# Guía del video demostrativo (evidencia por grabar)

1. Presentar Milk-V Duo S, NUCLEO-L432KC, adaptador USB-UART y conexiones SPI (0:00–0:30).
2. Mostrar `pio run` / `pio run -t upload` y que se verifica la carga (0:30–1:00).
3. Mostrar `./preparar_gpio.sh` y `python3 app.py --once --preset 2` con trama CRC válida (1:00–1:30).
4. Mostrar dashboard servido desde la IP USB de Milk-V, mediante Nginx, y dos canales ADC (1:30–2:20).
5. Alternar presets 100,1000,10000 Sa/s, evidencia de medición de tasa, descarga CSV (2:20–3:10).
6. Medir/explicar la tasa real de enlace SPI y límites de bitbang; registrar las restricciones (3:10–3:40).
7. Mostrar matriz de verificación, repositorio Git, roles, declaración IA y resultados (3:40–4:00).

No simular resultados reales; grabar pantalla, placas e instrumentos.
