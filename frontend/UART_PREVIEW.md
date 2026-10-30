# Vista UART experimental (NO forma parte del contrato HTTP)

Este experimento no sustituye `/api/v1/...`, ni implica que la Raspberry Pi transmita realmente. El equipo no ha aprobado un formato UART Pi → navegador. No editar firmware, backend ni SPI para acomodarlo.

## Supuestos de laboratorio

- Para este prototipo se configura UART a **115200 baudios, 8N1**, según la velocidad indicada. Ambos extremos deben usar la misma velocidad.
- Para que un navegador de Windows lea el UART de una Raspberry Pi se requiere una conexión física accesible como puerto COM (por ejemplo, un adaptador USB-UART compatible **3,3 V**). Compartir GND y cruzar TX del emisor a RX del receptor; nunca conectar directamente niveles RS-232 ni introducir 5 V a un GPIO Pi.
- Si el navegador se ejecuta en otro equipo y la Raspberry Pi está conectada solamente a la red, Web Serial **no puede abrir a distancia** el UART de la Pi. La arquitectura formal necesita un puente en el proceso Linux de Pipe y la API HTTP del proyecto.

## Abrir

Desde la raíz del repo: `node frontend/server.mjs` y en un navegador con Web Serial abrir `http://127.0.0.1:8000/uart-preview.html`.

La página NO solicita permiso automáticamente. Usa **Elegir puerto UART** y selecciona un puerto COM real. Si no hay puerto, la interfaz sigue indicando ausencia de conexión verificada. Si el puerto abre y no llegan bytes, muestra "esperando datos" sin inventar muestras. El navegador debe soportar Web Serial en un contexto seguro como localhost/HTTPS.

## Formato de prueba opcional, NO negociado con Pipe

Si el emisor envía UTF-8 con **un objeto JSON por línea (`\n`)**, y el objeto cumple `validateWindow` (CH1/CH2, N >= 64, 12 bits, `adc_counts`, `source`), el dashboard experimental dibuja la ventana. `window_id` debe ser entero positivo. El receptor puede leer bytes aunque el emisor utilice otro formato, pero no podrá dibujar la señal sin conocer su estructura.

Un JSON de ejemplo para el protocolo experimental se puede generar a partir de un fixture existente; el puerto debe enviar cada objeto completo en una sola línea. No afirmar que el contenido de un fixture es una medición real. El rótulo `hardware` recibido es una declaración del emisor, **no prueba** de origen físico.

## Pruebas

`node --test tests/unit/frontend/uart-lines.test.mjs`

La prueba local comprueba el acumulador de líneas; no comprueba un puerto físico, latencia de UART, caudal ni el protocolo de la Raspberry Pi.
