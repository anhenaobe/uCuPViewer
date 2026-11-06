# Corrección y validación del dashboard UART

Andrew autorizó corregir el inicio UART y continuar la prueba física del dashboard.
La comunicación SPI ya había pasado dos transferencias C y una Python.

## Defecto y cambio

El puente esperaba líneas que comenzaran por SCOPE_UID:0. La consola Bash de
Milk-V antepone CSI y OSC 3008 (integración de terminal) a la salida del comando.
Una lectura real de la cola del puente mostró:

```text
ESC[?2004l CR ESC]3008;start=...;type=command;cwd=/root/osciloscopio_final/milkv ESC\SCOPE_UID:0
```

Por eso startswith fallaba aunque Milk-V respondiera correctamente. Se añadió
console_line() en backend/milkv_uart/pc_dashboard_uart.py: elimina OSC terminados
por BEL o ESC\ y secuencias CSI antes de reconocer mensajes. Conserva JSON y
rechaza el eco del comando printf como confirmación. No se cambió el protocolo SC,
el firmware STM32, ADC ni los programas instalados en Milk-V.

## Verificación

```text
python -B -m unittest discover -s tests/milkv_uart -p test_*.py
12 tests: OK
git diff --check: sin errores
```

Se añadieron cuatro regresiones: respuesta UID con prefijo real, OSC/BEL y color,
eco que no constituye ACK, y lectura fragmentada con ACK y JSON. Son pruebas
offline y no sustituyen los resultados físicos siguientes.

Archivos copiados a /tmp/ucup-dashboard-check en la VM vmmm. Sin instalar
dependencias, se ejecutó el puente con Python 3 y el Prolific identificado.
El capturador milkv_stream.py se carga en memoria en la consola root de Milk-V;
solo este proceso controla SPI durante la prueba. osciloscopio.service estaba
inactive y no se arrancó. No se usó --demo.

Registro de inicio observado:

```text
Consola root de Milk-V detectada.
Capturador SPI activo en Milk-V. UART conectado.
Dashboard del computador: http://127.0.0.1:8080
Captura #4 válida: 1000 Sa/s, SPI 2.06 s, UART OK
Captura #5 válida: 1000 Sa/s, SPI 2.06 s, UART OK
```

Consultas reales vía túnel SSH desde Windows:

| Consulta | status | valid | source | sequence | cycle | muestras | error |
|---|---|---|---|---|---|---|---|
| Primera | ok | true | hardware | 12 | 9 | 64 | null |
| Posterior | ok | true | hardware | 28 | 23 | 64 | null |

La segunda consulta mostró mínimo CH1 RAW=4084 y máximo CH2 RAW=0. La página `/`
respondió HTTP 200 y 7812 caracteres HTML. Se verificó la ruta completa
STM32 → SPI GPIO → Milk-V → UART → puente en VM → API HTTP con datos reales y
avance de secuencia. La tasa 1000 Sa/s es la nominal del preset, no una medición.
No se validaron tensiones analógicas ni precisión de adquisición.

La herramienta de navegador informó que no hay navegador disponible; no se obtuvo
captura visual ni se verificó el dibujo de los canvas. La página y API sí
respondieron desde el computador anfitrión. No se confunde ese límite con una
inspección visual exitosa.

Una consulta posterior del registro contó 37 capturas válidas, cero mensajes
"Sin datos válidos" de SPI y **dos errores de interpretación JSON en UART**.
Los errores aparecieron después de las secuencias 21 y 29; la recepción se recuperó
en 24 y 32 respectivamente. Por tanto no se declara estabilidad continua ni
ausencia de pérdidas. La causa de esos mensajes dañados no se determinó en esta
corrección de inicio. El lector actual los registra y conserva el último estado
hasta la siguiente captura o el timeout de datos recientes; revisar integridad,
posibles mensajes de consola intercalados y pérdidas de bytes es una tarea posterior.

## Acceso y estado dejado para Andrew

Abrir en el PC Windows: http://127.0.0.1:18080/.
Consulta provisional: http://127.0.0.1:18080/api/state.
En la VM el servicio temporal escucha en http://127.0.0.1:8080/.

El dashboard sigue ejecutándose en la VM (PID observado 3211), con registro en
/tmp/ucup-dashboard-check/dashboard-fixed.log. Mantiene ocupado el UART y ejecuta
capturas SPI. No abrir Minicom ni otro maestro simultáneamente.
El túnel SSH Windows:18080 → VM:8080 permanece abierto para permitir visualización;
la regla NAT localhost:22222 → SSH de VM también se conserva mientras sea necesaria.
Ambos accesos se limitan a localhost. Si se cierra el túnel, deja de funcionar
el acceso Windows aunque el proceso siga activo en la VM.

Para terminar, verificar primero el PID/comando en la VM y enviar SIGINT al
proceso del dashboard: su cierre manda Q al capturador remoto. Confirmar salida
del capturador, UART libre y CS alto/SCLK bajo antes de abrir otra consola. Si
persiste un proceso, identificarlo antes de iniciar otro. Cerrar después el túnel
y eliminar la regla milkv-debug-ssh como indica el procedimiento de recuperación.
Los archivos de /tmp no son instalación persistente: el código fuente y las
instrucciones quedan versionados y respaldados en el PC.

## Recuperaciones posteriores observadas

Tras desconectar y reconectar el USB, VirtualBox perdió la asignación del
Prolific. Se reasignó el dispositivo 067B:2303 a vmmm; su symlink estable pasó
a apuntar a ttyUSB1. El proceso anterior seguía ocupando HTTP y conservaba un
descriptor UART inválido. SIGINT no terminó ese proceso lanzado en segundo plano;
se verificó su identidad y se terminó con SIGTERM. Se envió Q al capturador remoto,
se comprobó el prompt root y se inició una sola instancia nueva del puente.
PID observado después de recuperar: 3623; log dashboard-recovered.log en la
misma carpeta temporal. La API volvió a indicar hardware/valid=true, 64 muestras,
secuencia 279. No reutilizar números PID sin comprobar el comando actual.

En otra incidencia el USB permanecía conectado y HTTP respondía, pero STM32
reportó 0x17. La configuración solicitada/medida era preset 3, 10000 Sa/s. Se
restauró el preset 2 por la API existente:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:18080/api/preset -ContentType 'application/json' -Body '{"preset":2}'
```

Después se confirmó status=ok, valid=true, source=hardware, preset solicitado y
medido 2, 1000 Sa/s nominales, 64 muestras, secuencia 370 y error=null; página
HTTP 200. No se modificó firmware ni señal de entrada. El error 0x17 corresponde
a periodo perdido durante la adquisición polling, no demuestra desconexión USB.
La operación a 10000 Sa/s sigue sin validación de estabilidad. Si HTTP funciona,
consultar primero /api/state antes de reiniciar todo.
