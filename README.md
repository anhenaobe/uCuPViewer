<<<<<<< Updated upstream
﻿# uCuPViewer — STM32 + Milk-V

Desarrollo actual del equipo: adquisición de dos canales en STM32L432KC, comunicación
SPI por GPIO con Milk-V y visualización HTTP. Milk-V reemplaza definitivamente a
Raspberry Pi4, descartada por problemas de conexión/inicialización.

**Estado:** código actual importado y compilación/pruebas offline disponibles; no
se ha validado físicamente esta integración. El ZIP implementa polling ADC y trama
SC264. La interfaz SPI convencional de la Milk-V del montaje no está disponible;
se conserva bit-banging. Causa/alcance de la restricción pendientes de evidencia.

## Código actual
- `firmware/stm32/spi_polling/`: firmware actual del ZIP, proyecto independiente.
- `backend/milkv_uart/`: capturador Milk-V GPIO y puente UART/HTTP PC.
- `frontend/uart_dashboard/`: dashboard del desarrollo importado.
- `tests/milkv_uart/`: pruebas offline del protocolo.

El servidor HTTP importado corre en PC; servir desde el SBC continúa pendiente.
El código identifica Milk-V Duo S y menciona Debian, pero modelo físico y sistema
instalado requieren confirmación. No se usa SPI hardware Milk-V como requisito.

## Documentación vigente del desarrollo
- [Arquitectura real y procedencia](docs/architecture/estado_actual.md).
- [SPI por software](docs/protocol/spi_software.md).
- [Trama SC264](docs/protocol/frame_sc.md).
- [Estado ADC y problemas pendientes](docs/reviews/estado_firmware.md).
- [Roles](docs/02_roles_responsabilidades.txt) y [flujo Git](docs/06_flujo_git.txt).

[Contrato v0.2](docs/03_contratos_interfaces_v0_2.txt) y [decisión anterior](docs/04_eleccion_mcu_y_pruebas.txt)
son propuestas previas. SC264 es referencia actual; revisión coordinada con Andrew,
Pipe, Ferxxo y Checho pendiente, sin imponer268 B ni cambiar paquetes silenciosamente.
Se mantienen requisitos100/1000/10000 Sa/s por canal; su precisión debe medirse.

## Implementación previa y preservación
`firmware/stm32/src/` conserva ADC+TIM2+DMA y sus evidencias anteriores. No se mezcla
con main polling; resolver esa coexistencia será tarea separada. Backend/frontend
preexistentes e infraestructura de otros integrantes no se sustituyen.
`reference/profesor/` conserva código atribuido al docente sin cambios.
La [matriz histórica](docs/05_matriz_verificacion_inicial.txt) y resultados de Checho
no se reinterpretan como validación del desarrollo actual.

## Comprobaciones sin placas
```
pio run -d firmware/stm32/spi_polling -e nucleo_l432kc
python -B tests/milkv_uart/test_protocol_offline.py
```
La rama de diagnóstico añade el handler SysTick que faltaba al firmware importado.
El [diagnóstico físico](docs/debug/milkv_spi_diagnostico.md) registra el bloqueo
en la STM32 conectada y las pruebas iniciales de recepción de ceros. Con autorización
de Andrew se programó la versión corregida: [tres transferencias físicas válidas](docs/debug/milkv_validacion_post_systick.md)
con CRC y secuencias consecutivas. La imagen anterior se conserva respaldada.
Las tasas ADC y tensiones de entrada siguen pendientes de validación.

Repositorio: [anhenaobe/uCuPViewer](https://github.com/anhenaobe/uCuPViewer).
Desarrollo por ramas/PR hacia main, sin sobrescribir aportes ni alterar PASS/FAIL
sin evidencia. ZIP original intacto fuera de Git; procedencia y autoría individual
no inferida se detallan en el documento de arquitectura.
=======
# uCuPViewer

Proyecto universitario de adquisición de dos señales analógicas con STM32L432KC y visualización HTTP desde Raspberry Pi 4 Model B.

## Estado actual

La rama `ferxxo` integra el firmware de adquisición ADC/TIM2/DMA y la preparación de infraestructura Linux/SPI. El firmware compila y hay evidencia de programación ST-LINK y pruebas de API ejecutadas en la NUCLEO-L432KC. No hay mediciones documentadas de cadencia, señales conocidas, SPI físico, despliegue en Raspberry Pi ni acceso HTTP de extremo a extremo.

El módulo `infrastructure/spi_protocol.py` contiene framing candidato, transporte y simulador. El backend FastAPI y el dashboard Chart.js ahora tienen un modo de demostración con datos simulados; no prueba hardware. El instalador y las plantillas de Nginx/systemd están preparados, pero todavía no se han ejecutado en la Pi. El servicio backend usa un entorno virtual. El puerto Nginx 5000 es provisional.

El contrato v0.2 sigue pendiente de aprobación. También están pendientes de confirmar el pinout y READY con Valeria/Andrew, puerto y entrypoint con Pipe, frontend con Mateo y criterios de medición con Checho. Consultar [resultados y pendientes de infraestructura](infrastructure/spi_network_test_results.md) y [evidencia del firmware](firmware/stm32/test/hardware-evidence.txt). No marcar pruebas físicas como PASS sin evidencia observada.

## Plataforma y firmware

La plataforma seleccionada es STM32L432KC; el proyecto PlatformIO está en `firmware/stm32/`. La configuración usa STM32Cube HAL y arquitectura bare-metal. Consulta [la guía del firmware](firmware/stm32/README.md), [la evidencia de build](firmware/stm32/test/build-evidence.txt) y [la evidencia de hardware](firmware/stm32/test/hardware-evidence.txt) para límites y verificaciones existentes.

## Demostración local (solo simulación)

En Ubuntu, desde la raíz del repositorio:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
python backend/main.py
```

El backend escucha en `127.0.0.1:5000`. Abre `frontend/index.html` en Chrome; Chart.js se carga desde jsDelivr, por lo que la gráfica requiere acceso a Internet. Los controles cambian el preset de la simulación, no el STM32. Para despliegue con Nginx/systemd en una Raspberry Pi, revisar `infrastructure/README.md`; no se ha realizado todavía en hardware.

## Contrato y documentación

- [Contrato de interfaces v0.2](docs/03_contratos_interfaces_v0_2.txt), aún propuesto y sujeto a aprobación.
- [Elección de MCU y pruebas](docs/04_eleccion_mcu_y_pruebas.txt) y [matriz inicial](docs/05_matriz_verificacion_inicial.txt).
- [Roles](docs/02_roles_responsabilidades.txt) y guías por integrante en `docs/por_integrante/`.
- [Plan de despliegue](infrastructure/deployment-plan.md), [checklist](infrastructure/checklist.md) y [registro de pruebas SPI/red](infrastructure/spi_network_test_results.md).
- [Flujo Git](docs/06_flujo_git.txt) y [registro de aportes e IA](docs/07_aportes_ia.txt).

## Estructura

- `firmware/stm32/`: adquisición ADC con temporizador y DMA, más prueba ejecutable en placa.
- `infrastructure/`: protocolo SPI candidato, simulador y plantillas de despliegue para Raspberry Pi.
- `backend/`: API FastAPI y simulador por defecto; acceso SPI real sigue pendiente.
- `frontend/`: dashboard Chart.js con presets y refresco configurables.
- `reference/profesor/`: fuentes y diagrama originales atribuidos al docente; no modificarlos ni atribuirlos al equipo.

Las decisiones de contrato requieren revisión de los responsables afectados. Conservar fuentes, scripts y configuración; excluir compilaciones, cachés y secretos. Ver [atribución de la referencia](reference/profesor/ORIGEN.txt).
>>>>>>> Stashed changes
