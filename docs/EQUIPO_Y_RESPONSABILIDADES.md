# Equipo y responsabilidades

**Proyecto:** uCuPViewer — osciloscopio didáctico de dos canales  
**Plataformas actuales:** Milk-V Duo S (SBC Linux) y STM32L432KC
(microcontrolador)  
**Estado:** distribución de trabajo propuesta (revisada al 2026-11-05), pendiente de confirmación
y cierre por los integrantes.

> Este documento describe **responsabilidades asignadas y entregables
> esperados**. No constituye una declaración de trabajo realizado. Los
> aportes efectivos se acreditan mediante archivos, commits, pull
> requests y evidencias de pruebas.

## 1. Distribución del equipo

| Integrante  | Área principal                  | Responsabilidad                                                                                                                     | Entregables esperados                                                                                  |
|:------------|:--------------------------------|:------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------|
| **Andrew**  | Coordinación técnica y firmware | Organizar la integración; implementar adquisición de CH1/CH2 en STM32L432KC, temporización, ADC por polling del firmware actual y comandos SPI del MCU (ADC+DMA se conserva como variante anterior).         | Firmware compilable, guía de programación, pruebas de adquisición y revisión de interfaces.            |
| **Valeria** | Hardware y señales analógicas   | Diseñar y comprobar el cableado, la alimentación, las entradas ADC y las señales SPI entre las placas; READY solo si se aprueba como mejora futura.                        | Esquema, pinout verificado, fotografías del montaje y mediciones eléctricas.                           |
| **Sergio**  | Calidad y verificación          | Mantener requisitos y matriz; definir criterios de aceptación; preparar, ejecutar y registrar pruebas con apoyo de cada subsistema. | Matriz, protocolos, scripts, resultados, evidencias e informe de verificación.                         |
| **Mateo**   | Frontend y dashboard            | Implementar visualización CH1/CH2, selección de tasa, actualización periódica y mensajes de estado/error.                           | Interfaz web, cliente API, pruebas visuales y documentación de uso.                                    |
| **Felipe**    | Backend Linux y API             | Implementar lectura y validación de ventanas SPI, control de capturas, almacenamiento de última ventana y API HTTP.                 | Servicio backend, parser, endpoints, pruebas unitarias y guía de ejecución.                            |
| **Juan Fernando**  | Infraestructura Linux y SPI     | Configurar Milk-V Duo S, enlace SPI por software en el entorno actual, publicación HTTP y arranque de servicios.                    | Transporte GPIO/SPI, configuración Nginx/Apache, despliegue reproducible y mediciones de comunicación. |

## 2. Alcance y criterio de entrega por integrante

### Andrew — Coordinación y firmware STM32

- Configurar el temporizador, ADC por polling y TIM2 para obtener **64 muestras por
  canal** a 100, 1.000 y 10.000 Sa/s.
- Mantener el protocolo actual SC264: preset en el primer byte MOSI,
  lectura de ventana y actualización de preset en la siguiente captura.
  Cualquier CMD/ACK/READY nuevo requiere decisión conjunta.
- Coordinar la integración y revisar cambios de contrato entre
  subsistemas.
- **Se considera entregado cuando:** el firmware compila, se puede
  cargar en la placa y existen registros de pruebas de captura y
  comunicación.

### Valeria — Hardware

- Documentar conexiones CH1/CH2, GND, alimentación, SCLK, MOSI, MISO, CS; una señal READY solo si se acuerda en una revisión futura.
- Comprobar niveles eléctricos y rangos permitidos de **cada pin
  concreto**, especialmente en la Milk-V Duo S.
- Preparar señales de referencia y registrar condiciones de medición.
- **Se considera entregado cuando:** hay un esquema reproducible, un
  montaje identificado y evidencia de comprobaciones eléctricas.

### Sergio — Verificación

- Mantener la correspondencia entre requisitos, criterios,
  procedimientos y resultados.
- Preparar mediciones de frecuencia de muestreo, integridad SPI,
  rendimiento de SPI por software, refresco HTTP e integración.
- Registrar tanto pruebas satisfactorias como fallidas o bloqueadas, con
  instrumento, fecha y versión.
- **Se considera entregado cuando:** cada requisito evaluado tiene
  resultado trazable y los requisitos pendientes permanecen
  identificados, sin resultados supuestos.

### Mateo — Frontend

- Mostrar dos canales con escalas y unidades coherentes, sin confundir
  cuentas ADC con voltios calibrados.
- Permitir seleccionar presets mediante la API y distinguir solicitud aceptada
  de preset reportado por la ventana siguiente y de tasa medida físicamente.
- Actualizar las gráficas cada 1–4 s e indicar datos simulados,
  obsoletos o desconexión.
- **Se considera entregado cuando:** el dashboard funciona con la API
  acordada y dispone de evidencia de sus pruebas.

### Felipe — Backend y API

- Implementar el cliente del protocolo SPI, el análisis de tramas y la
  validación de integridad.
- Serializar el acceso al enlace y publicar únicamente ventanas
  completas y válidas.
- Implementar las rutas HTTP de estado, última ventana y cambio de
  preset, con errores explícitos.
- **Se considera entregado cuando:** los endpoints y el parser pasan
  pruebas unitarias y se demuestra una lectura física cuando la
  integración esté disponible.

### Juan Fernando — Linux, SPI e infraestructura

- Documentar imagen, kernel, arquitectura, pinout y método GPIO
  utilizado en la **Milk-V Duo S**.
- Implementar o integrar el transporte SPI por software con Felipe y
  Andrew; medir reloj, latencia, errores y rendimiento útil.
- Configurar Nginx o Apache y el mecanismo de inicio disponible en la
  imagen Linux real.
- **Se considera entregado cuando:** el despliegue es reproducible,
  existe comunicación SPI verificada y el dashboard es accesible por
  HTTP desde otro equipo.

## 3. Coordinación entre áreas

| Actividad compartida                       | Participantes                                               | Acuerdo o evidencia esperada                                                    |
|:-------------------------------------------|:------------------------------------------------------------|:--------------------------------------------------------------------------------|
| Contrato SPI, comandos, tramas y errores   | Andrew, Felipe, Juan Fernando; revisión de Sergio                    | Versión única del contrato y pruebas de compatibilidad.                         |
| Pinout, protección y adquisición analógica | Valeria, Andrew, Sergio                                     | Montaje seguro, tasas medidas y capturas identificadas.                         |
| API y presentación de datos                | Felipe, Mateo                                                 | JSON y estados consistentes, probados con datos simulados y luego reales.       |
| Rendimiento de SPI por software            | Juan Fernando, Felipe, Sergio                                        | Tiempos de transferencia, integridad y comparación con el presupuesto temporal. |
| Prueba extremo a extremo y demostración    | Todo el equipo; coordinación de Andrew y registro de Sergio | Señales reales → STM32 → SPI → Milk-V → HTTP → navegador.                       |

## 4. Organización en GitHub

| Área                                | Ruta sugerida     | Responsable principal |
|:------------------------------------|:------------------|:----------------------|
| Firmware del microcontrolador       | `firmware/`       | Andrew                |
| Esquemas y montaje                  | `hardware/`       | Valeria               |
| Matriz, protocolos y evidencias     | `docs/`, `tests/` | Sergio                |
| Dashboard                           | `frontend/`       | Mateo                 |
| Servicio y API                      | `backend/`        | Felipe                  |
| Configuración Linux, red y SPI GPIO | `infrastructure/` | Juan Fernando                |

**Flujo de trabajo:** issue o tarea definida → rama de trabajo → commits
identificables → pruebas → pull request → revisión → integración en
`main`.

La rama `verificationmatrix` contiene principalmente documentación de
requisitos y verificación. No sustituye las ramas de implementación ni
acredita automáticamente el trabajo de los demás.



## 7. Nota sobre la evidencia actual

El repositorio documenta tres tramas SPI válidas, pruebas offline y una ruta de datos UART/HTTP en PC. Esos logros **no equivalen a validación de tasas reales** a 100/1000/10000 Sa/s ni a un servidor HTTP demostrado en la Milk-V. La asignación de archivos a personas se acredita solo mediante commits/PR verificados y revisión de cada integrante; véase `APORTES_INDIVIDUALES.md`.
