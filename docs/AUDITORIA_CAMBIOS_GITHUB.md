# Auditoría de cambios para QA — uCuPViewer

**Fecha de consulta:** 2026-11-05 (America/Bogota). **Rama auditada:** `main`. **Commit confirmado mediante API de refs:** [`af58fc55793495d0e4d527ebfa83273e8443e33f`](https://github.com/anhenaobe/uCuPViewer/commit/af58fc55793495d0e4d527ebfa83273e8443e33f). **Base documental del ZIP recibido:** [`41601d45f7`](https://github.com/anhenaobe/uCuPViewer/commit/41601d45f71fb994444670fc85fe28a7be1d0a50).

## Diferencias verificadas

La comparación entre ambos commits informa **2 commits posteriores** y **51 archivos añadidos**, todos bajo `reference/prueba_1` a `reference/prueba_6`; no registra modificaciones ni eliminaciones de los archivos del código activo en esa comparación. Los archivos originales de firmware, backend, documentación de depuración y pruebas `tests/milkv_uart/` permanecen en el árbol del commit consultado.

| Carpeta | Qué aporta | Interpretación QA |
|---|---|---|
| `reference/prueba_1` | Prototipo SPI de **260 bytes**, versión anterior a SC264 | Referencia histórica; no sustituye el contrato vigente de 264 bytes |
| `reference/prueba_2` | Código diagnóstico SPI/ADC | Procedimiento/código, no aceptación del sistema |
| `reference/prueba_3` | Variante STM32 y puente PC/UART | No demuestra servidor HTTP alojado en Milk-V |
| `reference/prueba_4` | Variante de puente UART y preparación GPIO | Requiere resultados instrumentales |
| `reference/prueba_5` | Propuesta integral con ADC disparado por TIM2/DMA, app SBC, Nginx y tests | El README declara integración física pendiente. Su `docs/MATRIZ_VERIFICACION.csv` conserva V01–V16 como `PENDIENTE` y V17 como `NO_IMPLEMENTADO` |
| `reference/prueba_6` | Plan de rescate ADC por USB ST-LINK/PC | Su documentación expresa que **no utiliza Milk-V ni SPI**, por tanto no verifica esos requisitos |

## Interpretación y alcance

- **No alterar automáticamente** `RV-01` a `RV-38`, ni los estados del CSV de trazabilidad; su respaldo original es el historial de `41601d45f7`.
- Revisar `RV-05/06/07/08` (tasas y jitter): los nuevos ejemplos contienen configuración nominal, pero no aportan medición independiente de las tres tasas. Mantener incidencia `0x17` a 10 kSa/s en la implementación antigua hasta repetición.
- Revisar `RV-10/13` (SPI): no sumar los ejemplos como transferencias físicas completadas; los tres registros anteriores son la evidencia acotada existente.
- Revisar `RV-14/15/16` (HTTP, Nginx, refresco): `reference/prueba_5` contiene archivos de despliegue, **no evidencia de despliegue real** sobre Milk-V. La implementación candidata puede registrarse como alternativa, no como verificada.
- Revisar `RV-19/20` (tests/integración): el test offline de `reference/prueba_5/tests/test_protocolo.py` puede ejecutarse **separadamente**; un resultado OK no sustituye campaña física ni integra automáticamente esta variante al código activo.
- Existen PR #3, #4 y #7 abiertos en la consulta; sus cambios no deben atribuirse a `main`. PR #11 figura como `merged`, pero su implementación no aparece incorporada en la comparación de árboles de `main` desde la revisión base; verificar historia y contenido antes de citarla como activa. PR #10 y #12 corresponden a la incorporación de pruebas de referencia.

## Acciones antes de publicar QA

1. Confirmar con el equipo **cuál de las variantes de `reference/` es el firmware/backend realmente grabado y desplegado**, con hash de commit o binario. No asumir que `reference/prueba_5` es la implementación activa por llamarse final.
2. Mantener como evidencia histórica los links anclados al commit base; actualizar la etiqueta de revisión mediante esta nota, no cambiando indiscriminadamente el SHA dentro de URLs.
3. Registrar toda prueba nueva en `tests/results/registro_pruebas.csv` con fecha, versión, responsable, instrumento, resultado, datos y vínculo. En ausencia de ejecución, `NOT_RUN` o `BLOCKED`.
4. Medir tasas por canal con instrumento independiente; comprobar SCI/CRC, GPIO, fuente ADC, tiempos SPI, HTTP en SBC y refresco en navegador.
5. Cuando se seleccione definitivamente un candidato de `reference/`, actualizar el campo `Fuente en main` y el estado de implementación de **cada** RV afectado, documentando el cambio de contrato (especialmente 260 vs 264 bytes).
6. Revalidar el contenido del PR QA frente a `main` inmediatamente antes de fusionarlo.

**Nota:** la revisión es estática, de archivos e historial. No se dispone aquí de placas/instrumentos; **no se ejecutaron pruebas físicas ni se certificó una versión en campo**.
