# Ensayos, evidencias y resultado final

**Proyecto:** uCuPViewer · **Base:** [`main` 41601d45f7](https://github.com/anhenaobe/uCuPViewer/commit/41601d45f71fb994444670fc85fe28a7be1d0a50) · **Responsable de consolidación:** QA (`verificationmatrix`).

El repositorio **ya tiene** `tests/milkv_uart/test_protocol_offline.py` y `tests/milkv_uart/test_uart_console.py`, provenientes de otros aportes. Este paquete **no los sobrescribe** ni se atribuye su autoría.

## Archivos de verificación de esta rama

| Archivo | Propósito |
|---|---|
| [`../docs/MATRIZ_VERIFICACION.md`](../docs/MATRIZ_VERIFICACION.md) | 38 criterios con **código implementado**, **prueba realizada** y **resultado/alcance** independientes. |
| [`../docs/VERIFICACION_CODIGO_Y_EVIDENCIAS.md`](../docs/VERIFICACION_CODIGO_Y_EVIDENCIAS.md) | Extractos de código, pruebas SPI físicas, incidencias y casilla de video en Drive. |
| [`../docs/PROTOCOLOS_VERIFICACION_MILKV_DUOS.md`](../docs/PROTOCOLOS_VERIFICACION_MILKV_DUOS.md) | Procedimientos editables por ensayo F-* y D-*. |
| [`results/trazabilidad_requisitos.csv`](results/trazabilidad_requisitos.csv) | Misma clasificación de la matriz en formato tabular. |
| [`results/registro_pruebas.csv`](results/registro_pruebas.csv) | Registro **vacío** para cada nueva ejecución de ensayo. No se inventaron filas de medición. |
| [`report/INFORME_VERIFICACION.tex`](report/INFORME_VERIFICACION.tex) | Plantilla final para Overleaf/PDF, con espacios para tres presets y enlace al video. |
| `evidence/*` | Datos brutos, imágenes, registros y video/URL. |

## Organización de los archivos de evidencia

```text
tests/evidence/
  adc/           # Generador, mediciones temporales, RAW por canal, capturas
  spi/           # Analizador lógico, SCLK/MOSI/MISO/CS, trama binaria y CRC
  web/           # HTTP, consola, Network, Nginx/Apache, pantallas
  integration/   # Sesiones completas y logs de recuperación
  docs/          # Builds, inspección de código, esquemas, instrumentos
  video/         # Metadatos y autorizaciones de la grabación (video en Drive)
```

## Comandos seguros de comprobación offline

```bash
# Ejecutar desde la raíz del repositorio, sin conectar placas:
python3 -B -m unittest discover -s tests/milkv_uart -p 'test_*.py'

# Opcional, con PlatformIO instalado; compila pero NO programa:
pio run -d firmware/stm32/spi_polling -e nucleo_l432kc
```

**Precaución:** ambos comandos verifican software local; un `OK` o `SUCCESS` no demuestra ADC a la tasa real, niveles eléctricos, ni servidor HTTP en Milk-V. El informe previo registra doce tests offline OK; vuelve a ejecutar en tu propio commit y adjunta la salida antes de adjudicarte la ejecución.

## Plantilla de registro de nueva prueba

En `results/registro_pruebas.csv` completar una fila por intento, también si falla: ID, fecha, responsable, commit, preset, tipo de prueba, resultado, magnitudes, instrumento, enlace bruto y conclusiones. En `report/INFORME_VERIFICACION.tex` se incluyen fichas para mediciones ADC, SPI, HTTP y video.

## Video del osciloscopio

El lugar central para pegar URL Drive y marcas de tiempo es la [sección 8 del documento de evidencias](../docs/VERIFICACION_CODIGO_Y_EVIDENCIAS.md#8-video-de-demostracion-y-evidencia-en-google-drive). No se ha creado ni verificado enlace externo al preparar la rama.

## Revisión de novedades en GitHub

Se incorporaron seis paquetes de referencia bajo `reference/prueba_1` ... `reference/prueba_6`. **No los confundas con evidencias ejecutadas**. Ver `../docs/AUDITORIA_CAMBIOS_GITHUB.md`.
