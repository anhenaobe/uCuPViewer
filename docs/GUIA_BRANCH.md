# Instrucciones para subir esta documentación a `verificationmatrix`

Este paquete se diseñó para **copiar su contenido encima del clon existente de `uCuPViewer/`**, conservando las rutas `docs/` y `tests/`. **No** se debe crear una carpeta llamada `verificationmatrix/` dentro del proyecto, **no** borrar `backend/`, `firmware/`, etc. y **no** reemplazar el README principal automáticamente.

## 1. Inspeccionar y sincronizar sin perder trabajo

```bash
cd /ruta/a/uCuPViewer
git status --short
git fetch origin
git switch verificationmatrix
# Ejecutar solo si no hay cambios locales sin guardar y la rama permite fast-forward:
git merge --ff-only origin/main
```

Si `git switch` informa que no existe la rama local: `git switch --track origin/verificationmatrix`. Si `git status --short` muestra archivos locales, **no hagas merge a ciegas**: respáldalos fuera del clon o guarda una confirmación de cambios antes de integrar. Si `merge --ff-only` falla, no uses `reset --hard` ni `push --force`; resuelve el historial con el equipo.

## 2. Copiar contenido

Descomprimir `verificationmatrix_actualizado_2026-11-05.zip` **fuera** del clon. Copiar `docs/` y `tests/` del ZIP al `uCuPViewer/` clonado, fusionando carpetas (NO borrar las existentes). No copiar la carpeta contenedora `verificationmatrix_actualizado_2026-11-05/` como un nivel adicional. Conservar los tests del equipo en `tests/milkv_uart/` y todo el código preexistente.

## 3. Revisar el material y el video

- Abrir `docs/MATRIZ_VERIFICACION.md`: revisar cada estado `Código`, `Prueba realizada` y `Resultado` frente a la evidencia.
- Abrir `docs/VERIFICACION_CODIGO_Y_EVIDENCIAS.md`: allí hay extractos de código, pruebas SPI y el **espacio para pegar URL real de Drive**. Dejar explícito `PENDIENTE` si aún no hay video.
- El PDF de protocolos puede abrirse en GitHub; para editar, modificar el Markdown homónimo y volver a generar PDF.
- Completar aportes y declaración de IA únicamente con información comprobada.

## 4. Preparar y publicar cambios

```bash
git status --short
git add docs/ESPECIFICACION_MILKV_DUOS.md docs/MATRIZ_VERIFICACION.md \
  docs/VERIFICACION_CODIGO_Y_EVIDENCIAS.md \
  docs/PROTOCOLOS_VERIFICACION_MILKV_DUOS.md \
  docs/PROTOCOLOS_VERIFICACION_MILKV_DUOS.pdf \
  docs/PENDIENTES_ENTREGA.md docs/GUIA_BRANCH.md \
  docs/EQUIPO_Y_RESPONSABILIDADES.md docs/APORTES_INDIVIDUALES.md docs/USO_IA.md

git add tests/README.md tests/report/INFORME_VERIFICACION.tex \
  tests/report/INFORME_VERIFICACION_PLANTILLA.pdf \
  tests/results/trazabilidad_requisitos.csv tests/results/registro_pruebas.csv \
  tests/evidence/adc/.gitkeep tests/evidence/spi/.gitkeep \
  tests/evidence/web/.gitkeep tests/evidence/integration/.gitkeep \
  tests/evidence/docs/.gitkeep tests/evidence/video/.gitkeep

git diff --cached --check
git diff --cached --stat
git commit -m "docs(qa): actualizar matriz SC264 y evidencias de verificacion"
git push -u origin verificationmatrix
```

Los comandos están divididos en varias líneas para Bash, Git Bash o terminal Linux. En PowerShell puedes ejecutar cada `git add` en una sola línea o usar `git add docs/ tests/` tras revisar `git status`, **siempre que no existan archivos adicionales que no desees subir**.

## 5. Solicitar Pull Request

- GitHub → repositorio → `verificationmatrix` → `Compare & pull request`.
- **Base:** `main`. **Compare:** `verificationmatrix`.
- **Título sugerido:** `docs(qa): matriz SC264, evidencias de código y plan de video`.
- Resumen: 38 criterios con estados de implementación/prueba, SC264, transferencias SPI registradas, límite de integración PC/VM y plan de video de tres tasas.
- Advertencias: 100/1000/10000 Sa/s reales sin certificación; `0x17` a 10k; sin servidor HTTP verificado en SBC; video Drive aún pendiente.
- Revisores: Andrew, Valeria, Felipe, Juan Fernando y Mateo según documentación afectada.

## 6. Enlaces para añadir después al README principal (mediante PR)

```markdown
- [Especificación](docs/ESPECIFICACION_MILKV_DUOS.md)
- [Matriz de verificación](docs/MATRIZ_VERIFICACION.md)
- [Código, pruebas y video](docs/VERIFICACION_CODIGO_Y_EVIDENCIAS.md)
- [Protocolos de prueba (PDF)](docs/PROTOCOLOS_VERIFICACION_MILKV_DUOS.pdf)
- [Plan y registro de pruebas](tests/README.md)
```

**Base de consulta:** `main` SHA `41601d45f71fb994444670fc85fe28a7be1d0a50`. Antes de solicitar PR, revisar si `main` avanzó y si alguna evidencia cambió.

## Actualización previa al PR

Revisar `docs/AUDITORIA_CAMBIOS_GITHUB.md` y añadirlo al commit de QA con `git add docs/AUDITORIA_CAMBIOS_GITHUB.md`. No reinterpretar `reference/prueba_1` ... `prueba_6` como pruebas PASS; conservar los enlaces históricos y documentar por separado el último SHA auditado.
