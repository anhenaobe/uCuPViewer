# Frontend uCuPViewer

## Estado

Esta es una vista previa local de la fase 1. Usa fixtures sintéticos etiquetados como `simulated`; no consulta el backend y no representa una medición experimental.

## Requisitos

- Navegador moderno con soporte para módulos JavaScript.
- Node.js 18 o posterior para el servidor de vista previa local (no se requieren paquetes npm).

## Ejecución local

Desde la raíz del repositorio:

```powershell
node frontend/server.mjs
```

Abre `http://127.0.0.1:8000` en el navegador. Para detener el servidor, presiona `Ctrl+C` en la terminal. El servidor escucha solo en loopback y existe únicamente para la vista previa local.

## Vista previa

El selector carga uno de los fixtures `fixtures/window-*.json`. Cambia la escala temporal de la gráfica; no envía el POST de preset ni afirma que un dispositivo haya aplicado la frecuencia.

El eje horizontal usa `t[i] = i / sample_rate_hz`; el eje vertical presenta cuentas ADC de 12 bits. Cada gráfica corresponde a una ventana individual.

## Pruebas frontend

Desde la raíz del repositorio, ejecuta las pruebas de fixtures, validación y escala temporal con el runner integrado de Node.js:

```powershell
node --test tests/unit/frontend/validate.test.mjs tests/unit/frontend/time-axis.test.mjs
```

En la Raspberry Pi, Apache o Nginx debe servir el contenido estático según la configuración de infraestructura del equipo. `server.mjs` no sustituye ese requisito.
