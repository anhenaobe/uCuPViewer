# Infraestructura Linux

**Estado:** plan de despliegue. No hay servicios instalados ni pruebas de hardware o red registradas.

Esta carpeta prepara el despliegue en una Raspberry Pi 4 Model B para habilitar SPI y publicar el dashboard mediante Nginx. El sistema operativo, el kernel y los detalles de integración deben registrarse antes de cerrar una configuración concreta.

## Documentos

- [Plan de despliegue](deployment-plan.md): inventario, preparación de SPI y arquitectura HTTP.
- [Checklist de seguridad y verificación](checklist.md): controles y evidencias pendientes.

## Límites actuales

El contrato [v0.2](../docs/03_contratos_interfaces_v0_2.txt) sigue siendo una propuesta pendiente de aprobación y pruebas. Modo SPI 0, 8 bits, MSB-first y 1 MHz inicial son parámetros candidatos, no resultados medidos. READY, pines, separación entre transacciones y estados deben acordarse con hardware, firmware, backend y QA antes de implementar configuraciones o scripts.

No guardar credenciales, claves, tokens ni direcciones IP privadas sensibles en Git. Usar valores de ejemplo en documentación compartida.

## Fuentes oficiales

- [Raspberry Pi: habilitar SPI](https://www.raspberrypi.com/documentation/computers/configuration.html)
- [Raspberry Pi: hardware SPI y spidev](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html)
- [Nginx: módulo proxy](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
