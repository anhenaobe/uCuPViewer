# Componentes del desarrollo actual — contexto corregido
SPI por software es necesario en el montaje Milk-V y no se clasifica como descartable.
La evaluación anterior se sustituye por [estado_firmware.md](estado_firmware.md):
conservar CRC, serialización, ventanas, validación, bridge UART y dashboard; mejorar
arranque, waits y preparación TX mediante tareas posteriores acotadas.
SC264 se mantiene; no se requiere spidev, SPI hardware Milk-V ni conversión268 B.
La propuesta anterior queda únicamente en historial Git para trazabilidad.
