# Linux 2 · uCuPViewer

Proyecto universitario de adquisición de dos señales analógicas con STM32L432KC y visualización HTTP desde Raspberry Pi 4 Model B mediante SPI.

**Estado: planificación técnica; contrato v0.2 propuesto, pendiente de aprobación. Firmware, SPI, backend y dashboard todavía no están integrados ni validados. No hay resultados experimentales registrados.**

Repositorio existente: [anhenaobe/uCuPViewer](https://github.com/anhenaobe/uCuPViewer). `main` contiene la versión integrada; el desarrollo se presenta mediante ramas por tarea y Pull Requests.

## Plataforma seleccionada

STM32L432KC es la única plataforma de desarrollo. La evaluación inicial de Valeria favorece STM32 por ADC, temporización, DMA, SPI y simplicidad de integración. ESP32-S3 queda como comparación histórica, sin desarrollo ni pruebas obligatorias.

Decisión técnica inicial: Visual Studio Code + PlatformIO, STM32Cube HAL, CMSIS como soporte de bajo nivel y STM32 LL cuando convenga para periféricos críticos. Arquitectura bare-metal con máquina de estados, sin RTOS inicial. La justificación y fuentes están en [la nota técnica](docs/04_eleccion_mcu_y_pruebas.txt). No se ha creado `platformio.ini` ni firmware; la placa física, pinout, herramientas y versiones se confirmarán antes de configurarlos.

## Requisitos y acuerdos propuestos

- Dos canales ADC de 12 bits; ventana mínima de 64 muestras por canal, RAW en `uint16_t`, intercaladas CH1/CH2 y little-endian. La adquisición secuencial no implica simultaneidad.
- Presets de 100, 1.000 y 10.000 Sa/s por canal; 40.000 Sa/s por canal es un objetivo adicional sujeto a medición.
- Raspberry Pi controla SPI; STM32L432KC es periférico. Modo 0, 8 bits, MSB-first, CS bajo y SCLK inicial de 1 MHz son candidatos sin validación física.
- Dashboard servido por Apache o Nginx, con refresco entre 1 y 4 segundos, inicialmente 2 segundos. Esa cadencia es independiente de la adquisición ADC.
- Estimación teórica y contraste experimental de SPI; documentación, matriz de verificación, evidencias, video, aportes e interacciones con IA.

El [contrato activo v0.2](docs/03_contratos_interfaces_v0_2.txt) es la única fuente de detalles de trama y API. Captura terminada y transferencia SPI preparada son condiciones distintas. READY, tiempos y secuencia ACK siguen provisionales.

## Documentación

- [Revisión del esqueleto del profesor](docs/01_revision_esqueleto_profesor.txt).
- [Roles compartidos](docs/02_roles_responsabilidades.txt) y guías por integrante: [Andrew](docs/por_integrante/andrew.txt), [Valeria](docs/por_integrante/valeria.txt), [Checho](docs/por_integrante/checho.txt), [Mateo](docs/por_integrante/mateo.txt), [Pipe](docs/por_integrante/pipe.txt) y [Ferxxo](docs/por_integrante/ferxxo.txt).
- [Contrato v0.2](docs/03_contratos_interfaces_v0_2.txt), [elección técnica y ensayos previstos](docs/04_eleccion_mcu_y_pruebas.txt), [matriz de verificación](docs/05_matriz_verificacion_inicial.txt).
- [Flujo Git](docs/06_flujo_git.txt) y [registro de aportes e IA](docs/07_aportes_ia.txt).

## Estructura y próximo hito

- `firmware/stm32/`: espacio reservado para firmware futuro.
- `hardware/`: pinout, montaje y caracterización eléctrica futura.
- `backend/`, `frontend/`, `infrastructure/`: espacios de trabajo de Linux/SPI, dashboard y servicios HTTP; su existencia no demuestra funcionamiento.
- `tests/`: espacio para pruebas y evidencias futuras.
- `reference/profesor/`: fuentes C/C++/Rust y diagrama originales atribuidos al docente. No modificarlos ni atribuirlos al equipo.

Primero revisar contratos y placa/pines; después preparar configuración y pruebas con mocks mediante tareas separadas. Esta actualización solo documenta decisiones y prepara `.gitignore`; la implementación debe esperar revisión.

No sobrescribir trabajo de compañeros ni cambiar PASS/FAIL sin evidencia original. Los cambios de contratos requieren revisión de responsables afectados. Conservar fuentes, scripts, linker scripts y configuración propia; excluir compilaciones, cachés y secretos. Confirmar permiso del docente antes de redistribuir públicamente su referencia. Ver [atribución original](reference/profesor/ORIGEN.txt).
