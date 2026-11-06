# Traspaso a Codex en otro computador

## Instrucción de trabajo

Trabaja en anhenaobe/uCuPViewer. Andrew coordina firmware e integración. Recupera
la rama **debug/milkv-usb-access**, no solo main. Lee este documento y los
diagnósticos enlazados antes de actuar. Tu objetivo es repetir la recepción SPI,
comprobar su estabilidad y mostrar datos reales en terminal o dashboard. No
rediseñes el sistema ni programes la STM32 si sigue funcionando con la imagen
corregida. Confirma hardware conectado y entorno real antes de pruebas físicas.

## Estado comprobado y publicación

- STM32L432KC/NUCLEO-L432KC adquiere dos canales por polling; Milk-V Duo S SG2000
  controla SPI por GPIO. No usar Raspberry Pi, spidev, Device Tree ni recompilar
  kernel. Milk-V tiene CONFIG_SPI deshabilitado.
- Se corrigió SysTick, antes atrapado en Default_Handler con MISO bajo. Con
  autorización de Andrew se programó y verificó la versión del repositorio.
- Firmware corregido: commit 54a8396, `firmware/stm32/spi_polling/`, HAL/C,
  PlatformIO, sin RTOS. SysTick_Handler llama HAL_IncTick en archivo separado.
  **No confundir con firmware/stm32/src**, que conserva el desarrollo ADC+DMA
  anterior y usa PB3 como LED: no cargarlo con el cableado SPI actual.
- Evidencia b7fc24b: dos lecturas C y una Python, 264 B, SC, CRC válido, estado 0,
  64 pares y secuencias 1/2/3. CH1 RAW alrededor de 4080–4095, CH2=0. No se
  comprobaron tensiones, exactitud de tasas ni estabilidad prolongada.
- [Validación física](milkv_validacion_post_systick.md) es posterior al
  [diagnóstico inicial](milkv_spi_diagnostico.md). No interpretar las advertencias
  históricas de no flasheado como estado actual.
- GitHub contiene esos commits en debug/milkv-usb-access. Al preparar este traspaso,
  main seguía en 10ec48f; no se fusionó. La integración previa tiene PR #8, pero
  no debe asumirse que ese PR incluye la corrección posterior de esta rama.

**No todo el contenido de los dispositivos está en GitHub.** El firmware fuente
corregido, la variante UART del ZIP, tests y documentación sí están versionados.
Los archivos instalados en Milk-V (`spi_master.c`, `spi_master.py`, `protocolo.py`,
`app.py`, `preparar_gpio.sh`, servicio y dashboard de esa variante) fueron leídos
y sus hashes documentados; no se importaron completos. Respalda esa carpeta antes
de editar. Sus versiones difieren de backend/milkv_uart del repositorio.
Tampoco se publican Flash/binarios generados, ZIP original, credenciales ni cachés.

## Obtener la versión correcta

En un directorio nuevo, si no hay checkout:

```sh
git clone --branch debug/milkv-usb-access https://github.com/anhenaobe/uCuPViewer.git
cd uCuPViewer
git status --short --branch
git log -4 --oneline
```

Si ya hay checkout, inspeccionar status/ramas y hacer fetch. Con cambios locales,
usar otro worktree; no reset/clean/stash automático ni sobrescribir trabajo.
Crear una rama de pruebas desde origin/debug/milkv-usb-access. No modificar main.
Compilación opcional, sin upload:

```sh
pio run -d firmware/stm32/spi_polling -e nucleo_l432kc
python3 -B tests/milkv_uart/test_protocol_offline.py
```

Build verificado: Flash 6908 B, RAM estática 496 B; ststm32 19.5.0, CubeL4 1.18.1,
GCC ARM 7.2.1. No actualizar versiones durante la comprobación.

## Acceso real y preparación

En el PC anterior Codex ejecutaba Windows, no Debian. COM11 Prolific 067B:2303
fallaba al abrir. Se usó VM VirtualBox vmmm Debian 13, que sí abrió el adaptador
como ttyUSB0. ST-LINK 0483:374B/COM9 era otro dispositivo. VM quedó encendida con
Prolific asignado, UART cerrado y redirección SSH temporal eliminada.
En el nuevo PC enumerar de nuevo; no asumir ttyUSB0 ni pedir esas contraseñas.

```sh
uname -a
lsusb
ls -l /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id/ 2>/dev/null
ip -br link
sudo fuser -v /dev/serial/by-id/<adaptador-identificado>
```

Abrir una sola consola 115200/8N1 sin flujo. Si no hay Minicom/PySerial, usar el
sondeo termios reproducible de [recuperación](milkv_procedimiento_recuperacion.md).
No abrir simultáneamente Minicom y otro capturador. No chmod 666.
Prompt confirmado previamente: root@duos, kernel 5.10.4-20240527-2+, Debian
Forky/Sid riscv64, directorio `/root/osciloscopio_final/milkv`. Verificarlo otra vez.

Antes de tocar GPIO comprobar servicio, procesos, fuentes y hashes. La sesión
terminó con osciloscopio.service inactive; no arrancarlo automáticamente.
Si está activo ahora, pedir autorización para detenerlo antes de ejecutar otro
maestro. No tocar Nginx ni preparar_gpio.sh automáticamente.

Cableado: Milk-V J3-19/GPIO461 MOSI→PB5/D11; J3-21/462 MISO←PB4/D12;
J3-23/463 SCLK→PB3/D13; J3-24/464 CS→PA4/A3; J3-25 GND común.
GPIO461/463/464 salidas, 462 entrada; reposo 0/0/1; active_low=0.
Pinmux VIVO_D8/D7/D6/D5 debe ser XGPIOB_13/14/15/16. Consultar con cvi_pinmux -r,
sin escribir mux. Ver instrucciones completas y valores leídos en el diagnóstico.

## Primera prueba: terminal en la Milk-V

Ejecutar en la consola **Milk-V**, no en el anfitrión. Requiere la carpeta instalada
y su binario existente; no volver a compilarlo o reemplazarlo antes de respaldar.
Servicio detenido, sin otro maestro y direcciones verificadas son precondiciones.

```sh
cd /root/osciloscopio_final/milkv
python3 -B - <<'PY'
import subprocess, time
from pathlib import Path
from protocolo import decode
previous = None
for attempt in range(3):
    try:
        cmd = ['./spi_master','2','200'] if attempt < 2 else ['python3','-B','spi_master.py','2']
        result = subprocess.run(cmd, capture_output=True, timeout=8)
        print('command', cmd, 'exit', result.returncode, 'length', len(result.stdout),
              'header', result.stdout[:8].hex(' '))
        print(result.stderr.decode(errors='replace'))
        result.check_returncode()
        data = decode(result.stdout)
        seq = data['sequence']
        if previous is not None and seq != (previous + 1) % 65536:
            raise RuntimeError('Secuencia inesperada')
        previous = seq
        print('VALID', seq, 'pairs', len(data['samples']),
              'first', data['samples'][0], 'last', data['samples'][-1])
    finally:
        for n, value in ((464,'1'), (463,'0'), (461,'0')):
            Path('/sys/class/gpio/gpio%d/value' % n).write_text(value)
    time.sleep(1)
PY
```

La secuencia no tiene que comenzar en 1; comprobar avance. decode exige SC,
264 bytes, CRC16 CCITT-FALSE, estado cero, preset válido y RAW≤4095. Formato:
6 B cabecera + 256 B de 64 pares uint16 LE + 2 B CRC LE. No imponer 268 B.
No imprimir directamente la salida binaria de spi_master en UART.

Si falla: guardar comando, cabecera, longitud, stderr y estado GPIO. No ocultar
errores ni generar datos simulados. Revisar firmware/vector SysTick por lectura
antes de flashear; el respaldo original permite recuperación coordinada.

## Visualización: dos alternativas, nunca simultáneas

### A. Dashboard instalado en Milk-V

Esta variante tiene app.py y protocolo.py propios. Inspeccionar primero su código
y servicio; el código leído sirve `/`, `/api/state` y `/api/csv`, usa puerto 8080 y
selecciona el maestro C si su ejecutable existe. **No se validó físicamente el
dashboard durante la recuperación**, solo sus maestros y parser.

Tras cerrar la prueba manual y acordar el arranque temporal, con el servicio aún
detenido, ejecutar en primer plano en Milk-V:

```sh
cd /root/osciloscopio_final/milkv
python3 -B app.py --host 127.0.0.1 --port 8080
```

Usar otra sesión Linux de la Milk-V para `curl -fsS http://127.0.0.1:8080/api/state`.
Si solo hay una consola UART, no abrirla dos veces: preferir alternativa B o una
conexión SSH ya verificada. Si existe SSH a Milk-V por una red comprobada, se puede
abrir túnel desde PC `ssh -N -L 8080:127.0.0.1:8080 <cuenta>@<IP-verificada>` y
visitar http://127.0.0.1:8080. No asumir Ethernet/USB Gadget/IP predeterminada.
No publicar un puerto a toda la red ni modificar Nginx para esta prueba.
Al terminar, Ctrl+C y confirmar que no queda un hijo spi_master ni CS bajo.

### B. Dashboard provisional por UART, sin red hacia Milk-V

Disponible en el repositorio. Se ejecuta en **PC Debian o VM Debian**, no PowerShell:
usa stty y descriptores POSIX. Requiere consola Milk-V autenticada como root y luego
cerrar Minicom sin cerrar sesión Linux. Servicio/app/maestros Milk-V deben estar
detenidos. Este puente carga milkv_stream.py en memoria y empieza a generar SPI;
no es un simple lector pasivo. No hace falta copiar archivos a la microSD.

Desde la raíz del checkout en el PC Linux:

```sh
sudo python3 -B backend/milkv_uart/pc_dashboard_uart.py \
  --serial /dev/serial/by-id/<adaptador-identificado> --http-port 8080
```

Abrir navegador del **mismo PC/VM** en http://127.0.0.1:8080; en otra terminal de
ese PC: `curl -fsS http://127.0.0.1:8080/api/state`. No usar --demo: es simulación.
La variante UART debe reportar source=hardware, valid=true, secuencia que avanza y
64 muestras; la variante app.py usa ok=true/status=correcto. No confundir sus APIs.
El puente UART/dashboard todavía necesita esta prueba física; los tres resultados
anteriores no lo validan automáticamente. Cerrar con Ctrl+C; comprobar que Q terminó
el capturador remoto, recuperar prompt y confirmar reposo GPIO. Si el cierre falla,
no iniciar otro maestro: identificar el proceso antes de actuar.

## Después de las primeras capturas

1. Repetir unas 30 ventanas a preset 2 con un único maestro y registrar duración,
   errores, secuencias, CRC y rangos RAW. No llamar esto una prueba exhaustiva.
2. Con Andrew, medir dos tensiones conocidas y distintas, dentro de límites ADC,
   con GND común. No conectar señales negativas ni superiores a los límites.
   No cambiar cables ni puentear salidas sin explicar y autorizar la prueba.
3. Probar presets 1/2/3: el primer byte MOSI aplica a la captura SIGUIENTE; esperar
   la respuesta con preset deseado antes de atribuirle datos. Dejar margen entre
   transacciones para 64 muestras a 100 Sa/s (640 ms nominales más ejecución).
4. Medir temporización con instrumento: el timestamp i/rate del parser y la
   cadencia HTTP no prueban la tasa ADC. No afirmar 100/1000/10000 verificados
   por recibir paquetes; no activar 40000 ni migrar ADC a DMA en esta tarea.
5. Documentar resultados nuevos por separado, sin cambiar evidencias de Checho,
   profesores o pruebas anteriores. No fusionar automáticamente.

## Registro y respaldo en el PC anterior

Worktree actualizado: `C:\dev\7mo\Linux\milk-review-20261105`.
Copia original: `C:\dev\7mo\Linux\Linux2_uCuPViewer_inicio\Linux2_uCuPViewer_inicio`,
conservada en su rama anterior y con `firmware/stm32/.gitignore` sin seguimiento.
No se sobrescribió ni se hizo checkout sobre ese archivo.

Respaldo de traspaso local: `C:\dev\7mo\Linux\respaldo_ucupviewer_traspaso_20261105`.
Contiene bundle Git, snapshot de la rama, firmware corregido ELF/BIN, Flash anterior,
ZIP original, copia del .gitignore local y manifiesto SHA256. No contiene contraseñas.
Transferir ese respaldo por un medio del equipo si se necesita recuperar binarios;
no está publicado en GitHub. git bundle permite recuperar historia/ramas incluso
sin red; el snapshot permite leer los archivos sin depender del worktree.

Antes de terminar el trabajo del nuevo Codex: guardar resultados, git diff --check,
commit y push de su rama; informar qué se probó físicamente, qué se simuló, si se
usó dashboard y qué servicios/procesos quedaron activos. Detenerse tras validar
comunicación/visualización; no implementar todo el osciloscopio.
