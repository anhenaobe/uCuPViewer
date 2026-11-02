# Checklist de seguridad y verificación

Todos los puntos comienzan como pendientes. Completar con observaciones y evidencia antes de marcarlos PASS.

## Antes de conectar SPI

- [ ] Raspberry Pi 4 Model B y revisión de la placa física registradas.
- [ ] Distribución, versión del SO, kernel y arquitectura registrados.
- [ ] Valeria confirmó pines físicos/BCM, GND común, CS, SCLK, MOSI, MISO y READY si se acuerda usarla.
- [ ] Confirmados niveles GPIO compatibles de 3,3 V y ausencia de conflictos de pines.
- [ ] SPI habilitado y nodo `/dev/spidev*` presente; permisos y usuario que lo necesita registrados.
- [ ] Protocolo, temporización, separación de transacciones, timeout/retry y estados acordados por responsables; versión del contrato anotada.

## Despliegue y acceso de red

- [ ] Nginx/Apache elegido con responsables de backend y frontend; versión registrada al instalarlo.
- [ ] El servidor sirve el frontend y enruta `/api/` a la ruta y puerto acordados.
- [ ] Backend escucha en loopback, salvo decisión documentada que justifique otra interfaz.
- [ ] Backend corre con usuario no privilegiado y permisos mínimos para SPI/GPIO.
- [ ] No hay secretos, claves, tokens ni IP privada sensible en archivos versionados.
- [ ] Alcance de firewall/router revisado; no se habilitó acceso desde Internet por defecto.
- [ ] Acceso HTTP comprobado desde un segundo dispositivo de la LAN.

## Pruebas y evidencias

- [ ] PING/ACK/CRC verificados según protocolo aprobado.
- [ ] 100 lecturas de ventana verificadas sin corrupción, longitud inesperada ni CRC incorrecto.
- [ ] SCLK medido con instrumento y registrado junto con la frecuencia solicitada.
- [ ] Backend y dashboard muestran desconexión/error si el MCU no está disponible; ningún mock se presenta como hardware real.
- [ ] Servicios habilitados y verificados tras reiniciar la Pi.
- [ ] Estado, logs y validación de configuración del servidor web revisados.
- [ ] Evidencia incluye fecha, hardware, versiones, procedimiento y resultado; no se marcaron pruebas no ejecutadas como PASS.

## Registro de resultados

| Prueba | Resultado/evidencia | Estado |
|---|---|---|
| SPI habilitado y `spidev` | Pendiente | NOT_RUN |
| PING/ACK/CRC | Pendiente | NOT_RUN |
| 100 ventanas y SCLK medido | Pendiente | NOT_RUN |
| Dashboard desde otro dispositivo | Pendiente | NOT_RUN |
| Servicios tras reiniciar la Pi | Pendiente | NOT_RUN |
