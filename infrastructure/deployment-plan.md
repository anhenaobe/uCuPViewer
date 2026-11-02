# Plan de despliegue en Raspberry Pi

## Estado y alcance

Este documento cubre la planificación y las plantillas de infraestructura solicitadas para Ferxxo. No implica que SPI, HTTP o el arranque automático funcionen. El instalador aún no se ha ejecutado en la Pi y no hay resultados físicos registrados.

Plataforma seleccionada por el equipo: Raspberry Pi 4 Model B. El sistema operativo y la revisión de la placa real aún se deben registrar.

## Inventario por completar en la Pi

| Dato | Valor |
|---|---|
| Modelo y revisión de placa | Raspberry Pi 4 Model B; verificar placa física |
| Distribución y versión del SO | Pendiente (`cat /etc/os-release`) |
| Kernel y arquitectura | Pendiente (`uname -a`) |
| Versión de Nginx | Pendiente de instalación y registro |
| Backend, puerto local y rutas API | Acordar con Pipe |
| Directorio y rutas del frontend | Acordar con Mateo |
| Pinout, CS y READY | Confirmar con Valeria y Andrew |
| Instrumento para medir SCLK | Pendiente de confirmar con Checho |
| Hostname/IP de prueba | Registrar en evidencia local; no publicar IP privada sensible |

## SPI: preparación y verificación

1. Confirmar con Valeria el pinout físico y BCM en ambos extremos, GND común, CS, SCLK, MOSI, MISO y si se usará READY. Verificar niveles de 3,3 V y conflictos de pines antes de conectar señales.
2. En Raspberry Pi OS, habilitar SPI mediante `sudo raspi-config` → Interface Options → SPI. La documentación oficial indica que la habilitación activa la interfaz y carga el módulo del kernel al arranque. Confirmar el procedimiento y la ruta de configuración de acuerdo con la versión de SO instalada.
3. Registrar `ls -l /dev/spidev*` y `lsmod | grep spi`. La presencia del nodo `spidev` no demuestra comunicación física con el MCU.
4. Revisar propietario, grupo y permisos del nodo `spidev`, además del usuario que ejecutará el backend. No asumir que el grupo se llama `spi`; cualquier cambio de grupo o regla de permisos depende de la imagen instalada.
5. Acordar con Andrew/Pipe la máquina de estados SPI, separación entre comando, ACK y lectura, timeouts y comportamiento ante error. El contrato v0.2 califica trama y respuestas como candidatas no validadas; no implementar esos bytes como contrato congelado.
6. Medir SCLK con instrumento. Registrar frecuencia solicitada y medida, modo, cableado, tamaño de transferencia, cantidad de ensayos y errores. La frecuencia configurada por software no reemplaza la medición física.
7. Marcar pruebas PASS solo con evidencia observada. No afirmar PING/ACK correcto, 100 ventanas sin corrupción ni tasa máxima sin haber realizado y documentado esas pruebas.

## HTTP: arquitectura propuesta

```text
Cliente en la LAN
       |
       | HTTP a hostname/IP de la Pi
       v
Nginx: archivos estáticos del frontend
       |-- /api/ --> backend local en 127.0.0.1:<puerto acordado>
       `-- otras rutas --> recursos de Mateo
```

Nginx es la opción inicial propuesta. Debe servir los recursos del dashboard y enrutar `/api/` al backend. El backend no debe exponerse directamente a la LAN sin una necesidad revisada por el equipo.

Antes de desplegar la configuración, acordar con Pipe el puerto, rutas y comportamiento de error del backend, y con Mateo el directorio y rutas del frontend. Revisar la semántica de `location` y `proxy_pass` para que la ruta API recibida por el backend coincida con el contrato. La directiva oficial `proxy_pass` admite destinos HTTP y permite transferir solicitudes a un servidor upstream.

## Servicios y operación futura

La unidad systemd incluida usa un usuario no privilegiado, directorio de trabajo y `Restart=always`; requiere que Pipe integre `backend/app.py` antes de poder arrancar. Mantener secretos fuera de unidades versionadas. Limitar los permisos SPI/GPIO a lo necesario y documentar su reversión.

La plantilla de unidad, la configuración de Nginx y el instalador están en esta carpeta. El instalador es para revisión/uso en una Raspberry Pi 4; aún no se ha ejecutado en la placa real. No habilita el backend mientras falte `backend/app.py`; no hay unidad operativa hasta que Pipe acuerde e integre su entrypoint. El frontend actual tampoco aporta aún un `index.html` desplegable.

Después de integrar backend/frontend, documentar versiones, validar `nginx -t`, consultar `systemctl status` y `journalctl`, reiniciar la Pi y confirmar acceso desde otro dispositivo de la LAN. La plantilla proxy usa puerto 8000 como valor provisional; coordinarlo con Pipe antes de desplegar.

## Evidencias pendientes

Registrar SO/kernel, hardware, pinout confirmado, configuración SPI, frecuencias solicitadas y medidas, transacciones y errores, versiones de servicios, endpoint API, acceso desde un segundo dispositivo, reinicio y logs pertinentes. Separar límites teóricos de resultados medidos. Hasta ejecutar estas pruebas, el estado es **pendiente**, no PASS.
