# Infraestructura Linux

**Estado:** plantillas y script preparados; no se han instalado en la Pi ni se han registrado pruebas de hardware o red.

Esta carpeta prepara el despliegue en una Raspberry Pi 4 Model B para habilitar SPI y publicar el dashboard mediante Nginx. El sistema operativo, el kernel y los detalles de integración deben registrarse antes de cerrar una configuración concreta.

## Contenido

- `spi_client.py`: framing CRC, parseo de ACK/ventanas y transporte `spidev` con modo 0, 8 bits, MSB-first, CS activo bajo y 1 MHz inicial.
- `nginx/ucupviewer.conf`: servidor estático y proxy `/api/` a loopback, puerto 8000 como valor provisional.
- `systemd/ucupviewer-backend.service`: plantilla para un backend Python en `backend/app.py`.
- `install_infra.sh`: instalador explícito para Raspberry Pi 4 con Nginx, `python3-spidev`, habilitación SPI y permisos de servicio.
- [Plan de despliegue](deployment-plan.md) y [checklist](checklist.md).

## Uso previsto

Desde la raíz de un checkout en la Raspberry Pi, ejecutar `sudo bash ./infrastructure/install_infra.sh`. El script modifica configuración del sistema, instala paquetes y habilita Nginx. Si falta `backend/app.py`, deja la unidad instalada pero no la habilita; cuando Pipe integre el backend y su entrypoint, volver a ejecutarlo para activar el servicio. El frontend también debe aportar `frontend/index.html` antes de que haya un dashboard que servir.

Para seleccionar el puerto acordado con Pipe: `sudo env UCUPVIEWER_BACKEND_PORT=8000 bash ./infrastructure/install_infra.sh`. El backend debe escuchar únicamente en `127.0.0.1`.

`SpiLink` expone transferencias separadas: `send_command(...)`, `receive_ack(opcode, sequence)` y `receive_window(sequence)`. Las dos últimas envían bytes dummy para producir reloj y recoger MISO. El llamador debe esperar entre fases según el handshake que se acuerde con firmware. El parser conserva el byte `status` sin asignarle significado porque sus valores aún no están congelados.

Ejemplo de la secuencia candidata (no ejecutar contra hardware hasta acordar estados y tiempos con Andrew/Pipe):

```python
from infrastructure.spi_client import OP_PING, OP_READ_WINDOW, SpiLink

sequence = 1
with SpiLink(bus=0, device=0) as link:
    link.send_command(OP_PING, sequence=sequence)
    ping_ack = link.receive_ack(OP_PING, sequence)
    # Interpretar ping_ack.status según el mapa de estados aprobado.

    read_sequence = (sequence + 1) & 0xFF
    link.send_command(OP_READ_WINDOW, sequence=read_sequence)
    read_ack = link.receive_ack(OP_READ_WINDOW, read_sequence)
    # Solicitar receive_window solo cuando el ACK confirme TX preparada.
    # window = link.receive_window(read_sequence)
```

## Límites y seguridad

El contrato [v0.2](../docs/03_contratos_interfaces_v0_2.txt) sigue siendo una propuesta pendiente de aprobación y pruebas. La trama y secuencia de transacciones están implementadas como candidatas para integración, no como enlace probado. READY/IRQ, tiempos de espera y estados deben acordarse con hardware, firmware, backend y QA. La lectura de ventana valida la estructura, CRC, secuencia, padding y valores ADC de 12 bits.

El script detecta Raspberry Pi 4 y usa `/boot/firmware/config.txt` o `/boot/config.txt` según exista; crea una copia de respaldo antes de cambiar `dtparam=spi=on`. Solo añade el usuario del servicio a los grupos `spi` y `gpio` si ya existen. Revisa permisos efectivos del nodo `spidev` en la Pi concreta. No guarda credenciales, claves, tokens ni direcciones IP privadas sensibles en Git.

La plantilla systemd usa usuario sin privilegios y `Restart=always`. No la habilita si el entrypoint del backend aún no existe. El script puede deshabilitar el enlace del sitio Nginx predeterminado del paquete; conserva un respaldo del enlace. No ejecutar en equipos que no sean la Pi de destino.

## Fuentes oficiales

- [Raspberry Pi: habilitar SPI](https://www.raspberrypi.com/documentation/computers/configuration.html)
- [Raspberry Pi: hardware SPI y spidev](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [Nginx: módulo proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Python `spidev`](https://github.com/doceme/py-spidev)
- [Linux: SPI userspace API](https://docs.kernel.org/spi/spidev.html)
