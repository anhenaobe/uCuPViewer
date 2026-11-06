# Trama SC — referencia de trabajo actual

Se conserva formato del ZIP, sin conversor ni migración a268 B. Fuentes:
firmware/stm32/spi_polling/src/main.c (put16,crc16,prepare_frame,slave_transfer) y
backend/milkv_uart/milkv_stream.py (crc16,capture).

| Offset inclusive | Tamaño | Campo |
|---|---|---|
|0..1|2|ASCII SC =53 43 hexadecimal|
|2|1|preset1=100,2=1000,3=10000 Sa/s nominales/canal|
|3|1|estado0 éxito; errores ADC/temporización10..17 hex|
|4..5|2|contador de ventana uint16 little-endian|
|6..261|256|64 pares CH1/CH2, cada RAW12 en uint16 LE|
|262..263|2|CRC16 CCITT-FALSE sobre bytes0..261, little-endian|

Total6+256+2=264 B. CH1[i] en6+4*i; CH2[i] en8+4*i. Sin padding.
CRC initFFFF, polinomio1021, sin reflexión ni xor final. No incluye bytes CRC.
SC es firma, no opcode. CS delimita una transferencia de264 B; no hay búsqueda
interna de firma para recuperar una trama desplazada. Milk-V rechaza cabecera,
CRC, preset desconocido, estado no cero y valores >4095. No detecta huecos de
secuencia ni vincula la respuesta a un ID de solicitud.

MOSI manda preset como primer byte, seguido de263 ceros. No está protegido por CRC
ni confirmado por ACK; aplica a la SIGUIENTE captura. Un código inválido conserva
el preset anterior. El contador se incrementa al preparar, incluso si ADC falla,
y desborda como uint16. Error permite payload incompleto/cero pero receptor lo rechaza.

## Ejemplo sintético completo y reproducible
No es medición: preset2,estado0,secuencia1; CH1[i]=i y CH2[i]=4095-i.
Cabecera53 43 02 00 01 00. Primer par00 00 FF 0F; último3F 00 C0 0F.
La función frame() de tests/milkv_uart/test_protocol_offline.py genera todos los
264 bytes y calcula CRC; el test_frame comprueba que capture recupera ambos arrays.
Vector independiente CRC("123456789")=29B1. No se confunde fixture con adquisición.

## Diferencias con propuesta anterior v0.2
| Campo | SC actual | v0.2 anterior | Acción de coordinación |
|---|---|---|---|
|Total|264|268|Elegir contrato revisado, no asumir migración|
|Cabecera|6|8|Documentar diferencias explícitas|
|Firma|SC2 bytes|5A1 byte|Incompatibles|
|Preset|byte2,IDs1/2/3|byte3,IDs0/1/2/3|Acordar mapa;40k no activo|
|Estado|byte3,10..17 errores|byte1,0OK/resto pendientes|Acordar semántica|
|Secuencia|uint16 en4..5|byte2 eco solicitud|Distinta identidad|
|N|implícito64|uint16 en4..5|SC es tamaño fijo|
|Bytes payload|implícito256|uint16 en6..7|Receptor SC asume tamaño|
|Payload|6..261|8..263|Mismo orden de pares/LE|
|CRC|262..263 sobre0..261|264..265 sobre0..263|Mismo algoritmo, rango distinto|
|Padding|0 B|2 B ceros|Dos de los cuatro bytes de diferencia|
|Comandos|preset primer MOSI|CMD8 B conCRC,ACK8 B|Flujos incompatibles|

Diferencia4 B =2 B más de cabecera +2 B padding; no CRC adicional.
SC264 es la referencia actual. v0.2 queda identificada como propuesta histórica;
revisión de requisitos por Andrew, Pipe, Ferxxo y Checho pendiente. Ni campos ni
bytes cambian en esta tarea. El adaptador infrastructure/spi_protocol.py anterior
no debe conectarse a este desarrollo suponiendo compatibilidad.
