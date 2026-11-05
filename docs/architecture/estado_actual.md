# Estado actual de uCuPViewer

Actualizado 2026-11-05 con aclaración de Andrew: el ZIP es desarrollo actual del
equipo. Milk-V reemplaza definitivamente a Raspberry Pi 4, descartada por problemas
de conexión/inicialización. No se atribuye autoría individual sin registro.

## Arquitectura real y código
| Subsistema | Ruta | Estado |
|---|---|---|
| STM32 actual polling y SPI GPIO | firmware/stm32/spi_polling/src/main.c | Importado sin modificar; compilable; bloqueo de arranque pendiente |
| Controlador Milk-V GPIO | backend/milkv_uart/milkv_stream.py | Python3; controlador SPI y emisión JSON UART |
| Puente UART/HTTP PC | backend/milkv_uart/pc_dashboard_uart.py | Carga programa Milk-V por consola root; sirve HTTP en PC |
| Dashboard actual | frontend/uart_dashboard/dashboard.html | HTML/JS importado; consume servidor PC |
| ADC+TIM2+DMA anterior | firmware/stm32/src/ | Conservado sin cambios; no se combina con polling |

Flujo: entradas PA0/PA1 → ADC STM32 → ventana SC264 → SPI GPIO Milk-V →
SCOPE_DATA por UART → puente PC → dashboard HTTP. En el desarrollo importado HTTP
está en PC, no en Milk-V: traslado del servicio al SBC sigue pendiente respecto al
requisito académico. Fuente: main.c prepare_frame/slave_transfer, milkv_stream
capture/main y pc_dashboard_uart SerialPort.install_remote/handle_data/HTTP handler.

El código declara NUCLEO-L432KC y Milk-V Duo S; el README original menciona Debian.
Modelo/revisión físicos de Milk-V y distribución instalada no verificados en esta
tarea. No inferir pinmux o límites eléctricos a partir de esos nombres.
SPI convencional de la Milk-V está no disponible/bloqueado en el montaje según
Andrew. Causa, alcance y evidencia de esa restricción pendientes de documentar;
no se generaliza a otros modelos. Bit-banging es la ruta operativa actual. No hay
requisito de spidev, Device Tree ni habilitación de SPI hardware de Milk-V.

## Integración y conflictos preservados
La raíz firmware/stm32 contiene otro main y módulos ADC+DMA. Reemplazarlo eliminaría
trabajo previo y cambiaría adquisición/pines; por ello el proyecto polling tiene
platformio.ini independiente. Es organización del desarrollo actual, no una copia
descartable ni firmware externo. La elección de un único punto de entrada futuro
es conflicto sustancial pendiente de revisión. No combinar src de ambos proyectos.
Backend/frontend nuevos están en carpetas propias; infraestructura y ramas de otros
integrantes no se fusionan. Cambio funcional de importación: ruta de dashboard.html
resuelta desde backend/milkv_uart a frontend/uart_dashboard. Paquetes y algoritmos
originales intactos. Instrucciones originales preservadas en zip_instrucciones_originales.md;
sus rutas Prueba_SPI/pc son históricas y no deben aplicarse como reemplazo automático.

## Procedencia y pruebas
ZIP: osciloscopio_uart_sin_ethernet.zip; SHA256
26084F7C02791D1B1908BE035845C370718E375F20AF2A5DD56DF53DF94E7059.
Aportado por Andrew como trabajo del equipo; no consta autor individual por archivo.
Se conservan comentarios y nombres originales. ZIP intacto fuera de Git; cachés
excluidas. No se agregan licencias ni créditos individuales supuestos.
Fuentes: README original, main.c y scripts importados; docs/protocol/frame_sc.md,
docs/protocol/spi_software.md y docs/reviews/estado_firmware.md detallan evidencia.

Demostrado aquí: compilación aislada, pruebas simuladas de parser/CRC e inspección
de ELF. No demuestra comunicación física ni tasa ADC. Las pruebas históricas del
firmware DMA permanecen intactas y no validan automáticamente el firmware polling.
Faltan preparar_gpio.sh, proyecto original completo Prueba_SPI, evidencia de pinmux,
mediciones temporales, entradas conocidas y captura de señales SPI. No se ejecutan
UART, GPIO ni programación de placas en esta tarea.

## Coordinación documental
v0.2 es propuesta anterior de268 B, no el formato del desarrollo actual. SC264 es
referencia de trabajo actual documentada sin cambiar sus bytes. Proponer revisión
coordinada con Andrew, Pipe, Ferxxo y Checho de plataforma, IDs, estados, ACK y HTTP.
No imponer268 B ni convertir protocolos en este PR. La matriz y evidencias de Checho
no se alteran; las referencias antiguas dentro de ellas son contexto histórico.
