# Auditoría SPI polling — actualización de contexto
La clasificación anterior del ZIP como prototipo externo queda corregida: Andrew
confirma que contiene el desarrollo actual del equipo. Fuentes ahora integradas
por subsistema, conservando SPI GPIO y SC264.

La auditoría técnica vigente está en [estado del firmware](estado_firmware.md),
[SPI software](../protocol/spi_software.md), [trama SC](../protocol/frame_sc.md) y
[arquitectura](../architecture/estado_actual.md). Conservan los hallazgos SysTick,
CS sin límite, TX sin handshake y diferencias de formato; su existencia no acredita
la causa física de la avería. La auditoría previa se conserva en historial Git.
