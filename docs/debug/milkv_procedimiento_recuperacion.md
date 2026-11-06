# Procedimiento de recuperación y prueba controlada

**Actualizaci?n posterior:** Andrew autoriz? programar la versi?n corregida; se obtuvieron tres transferencias f?sicas v?lidas. Ver [validaci?n posterior](milkv_validacion_post_systick.md). Las restricciones de programaci?n y resultados de fallo siguientes describen la sesi?n anterior.

Basado en la sesión del 5 de noviembre de 2026. Resultado de referencia:
[USB recuperado](milkv_usb_diagnostico.md), [SPI bloqueado por SysTick](milkv_spi_diagnostico.md).
No flashear la variante local hasta resolver su diferencia con la versión instalada.

## 1. Identificar el anfitrión y el USB

En Windows PowerShell:

```powershell
[Environment]::OSVersion.VersionString
Get-PnpDevice -PresentOnly | Where-Object InstanceId -Match 'VID_067B&PID_2303|VID_0483&PID_374B'
Get-ItemProperty HKLM:\HARDWARE\DEVICEMAP\SERIALCOMM
Get-NetAdapter
& 'C:\Program Files\VBoxManage.exe' list runningvms
& 'C:\Program Files\VBoxManage.exe' list usbhost
```

En esta sesión Prolific=COM11, ST-LINK=COM9; reenumerar, no asumir esos números.
COM11 falló antes de recibir bytes. No cambiar baud rate para intentar solucionar
un error de apertura del driver. No interpretar la presencia USB como consola útil.

Andrew autorizó usar `vmmm` y asignarle el Prolific. Si está apagada, arrancarla
con `VBoxManage startvm vmmm --type headless`. Consultar `list usbhost` y asignar
**el UUID vigente de 067b:2303**, no el ST-LINK:

```powershell
& 'C:\Program Files\VBoxManage.exe' controlvm vmmm usbattach '<UUID Prolific verificado>'
& 'C:\Program Files\VBoxManage.exe' showvminfo vmmm
```

En Debian anfitrión o VM:

```sh
uname -a
lsusb
ls -l /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id/ 2>/dev/null
ip -br link
id
sudo fuser -v /dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0
sudo dmesg | tail -30
```

Debe identificarse 067b:2303 y su symlink real. En esta sesión fue ttyUSB0,
root:dialout, modo 0660. Si está ocupado, identificar al dueño antes de abrirlo;
no matar procesos indiscriminadamente. No cambiar a chmod 666.

## 2. Obtener consola a 115200, 8N1, sin flujo

La VM no tenía PySerial/Minicom. Este sondeo usa solo la biblioteca estándar.
Guardar el siguiente texto **en la VM**, por ejemplo `/tmp/milkv_uart_probe.py`;
no lo instala en la Milk-V. Primero sin argumentos escucha pasivamente. Después
con `--prompt` envía un CR. No enviar órdenes Linux hasta identificar su prompt;
si responde U-Boot, registrar y detenerse sin ejecutar boot/setenv/saveenv.

```python
import fcntl
import os
import select
import sys
import termios
import time
import tty

port = '/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0'
fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
old = None
try:
    fcntl.ioctl(fd, termios.TIOCEXCL)
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    attrs = termios.tcgetattr(fd)
    attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
    attrs[4] = attrs[5] = termios.B115200
    termios.tcsetattr(fd, termios.TCSANOW, attrs)
    if len(sys.argv) > 1:
        command = '' if sys.argv[1] == '--prompt' else sys.argv[1]
        outgoing = (command + '\r').encode()
        while outgoing:
            if select.select([], [fd], [], 2)[1]:
                outgoing = outgoing[os.write(fd, outgoing):]
            else:
                raise TimeoutError('UART no admite escritura')
    until = time.monotonic() + 8
    data = bytearray()
    while time.monotonic() < until and len(data) < 100000:
        if select.select([fd], [], [], .2)[0]:
            data.extend(os.read(fd, 4096))
    print(data.decode('utf-8', 'replace'))
finally:
    if old is not None:
        termios.tcsetattr(fd, termios.TCSANOW, old)
    os.close(fd)
```

```sh
sudo python3 /tmp/milkv_uart_probe.py
sudo python3 /tmp/milkv_uart_probe.py --prompt
# Solo tras reconocer root@duos u otra consola Linux autenticada:
sudo python3 /tmp/milkv_uart_probe.py 'uname -a; cat /etc/os-release; pwd'
```

Cada sondeo cierra el puerto: no mantener otro terminal abierto a la vez. La
contraseña de la VM no se debe copiar a scripts, documentación ni comandos shell.
El prompt recuperado fue `root@duos:~/osciloscopio_final/milkv#`.

Para acceso SSH a la **VM**, se utilizó temporalmente:

```powershell
& 'C:\Program Files\VBoxManage.exe' controlvm vmmm natpf1 'milkv-debug-ssh,tcp,127.0.0.1,22222,,22'
ssh -o UserKnownHostsFile=C:/dev/7mo/Linux/milkv-debug-known-hosts -p 22222 vboxuser@127.0.0.1
```

Comprobar antes que el puerto esté libre, que ssh esté activo en la VM y comparar
la huella con `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` desde su consola.
La conexión SSH anterior termina en la VM, no en Milk-V. La sesión UART es el
segundo salto. No exponer el puerto a todas las interfaces.

## 3. Inspeccionar Milk-V sin modificarla

Ejecutar en su consola, o como argumento del sondeo anterior:

```sh
uname -a
cat /etc/os-release
date -Is
pwd
find /root /home -maxdepth 4 -name spi_master.c -o -name osciloscopio.service
findmnt -no SOURCE,FSTYPE,OPTIONS /
df -h /
systemctl status osciloscopio.service --no-pager -l
systemctl cat osciloscopio.service
journalctl -u osciloscopio.service -n 30 --no-pager
ps -eo pid,user,args | grep -E '[s]pi_master|[a]pp.py|[m]ilkv_stream'
```

No ejecutar instalar.sh ni reiniciar el servicio. Registrar la ruta encontrada y
comparar `sha256sum`, no solo fechas. En la sesión era
`/root/osciloscopio_final/milkv`; el servicio ya estaba inactive.

## 4. Verificar GPIO antes de generar pulsos

```sh
for n in 461 462 463 464; do
    printf '%s\n' "$n"
    cat /sys/class/gpio/gpio$n/direction
    cat /sys/class/gpio/gpio$n/value
    cat /sys/class/gpio/gpio$n/active_low
done
cvi_pinmux -r VIVO_D8
cvi_pinmux -r VIVO_D7
cvi_pinmux -r VIVO_D6
cvi_pinmux -r VIVO_D5
```

Esperado: MOSI461 out/0, MISO462 in, SCLK463 out/0, CS464 out/1; active_low=0;
XGPIOB_13/14/15/16 respectivamente. No ejecutar automáticamente preparar_gpio.sh:
cambia mux y direcciones. Ante discrepancias registrar y revisar antes de escribir.

Por ST-LINK identificado se puede consultar STM32 sin reset ni halt:

```text
openocd -s <scripts> -f interface/stlink.cfg
  -c "adapter serial 0672FF373146363143221241" -f target/stm32l4x.cfg
  -c "reset_config none" -c init -c targets
  -c "mdw 0xE000ED08 1" -c "mdw 0xE000ED04 1"
  -c "mdw 0x0000003C 1" -c "mdw 0x48000400 1"
  -c "mdw 0x48000000 1" -c shutdown
```

Lo anterior es una sola orden, presentada en varias líneas. En PowerShell usar
la ruta instalada `C:\Users\justa\.platformio\packages\tool-openocd\bin\openocd.exe`
y scripts en `...\tool-openocd\openocd\scripts`. Revalidar serie/objetivo antes
de cada uso. No conducir SCLK si PB3 aparece como salida. No conectar loopback
ni puentear GPIO de salida. Para instrumentación futura Andrew puede observar
pasivamente CS/SCLK/MOSI/MISO y GND común con analizador compatible con 3,3 V;
no es necesario modificar el cableado para el diagnóstico actual.

## 5. Prueba SPI acotada

Solo tras comprobar servicio detenido, ausencia de otro maestro, pinmux y
direcciones compatibles en ambas placas. Si el servicio está activo, solicitar
autorización antes de detenerlo; no iniciar un segundo maestro en paralelo.
El bloqueo SysTick ya está demostrado: repetir los ceros antes de corregirlo
no aporta validación de funcionamiento.

En la ruta instalada Milk-V, esta prueba guarda la respuesta en RAM, no en la SD:

```sh
python3 -B - <<'PY'
import subprocess
import time
from pathlib import Path
from protocolo import decode
for attempt in range(2):
    try:
        p = subprocess.run(['./spi_master', '2', '200'],
                           capture_output=True, timeout=8)
        print(attempt + 1, 'exit', p.returncode, 'length', len(p.stdout),
              'header', p.stdout[:8].hex(' '))
        print(p.stderr.decode(errors='replace'))
        if p.returncode:
            raise RuntimeError('Falló el maestro')
        try:
            data = decode(p.stdout)
            print('VALID', data['sequence'], len(data['samples']))
        except ValueError as e:
            print('INVALID', str(e))
    finally:
        # Valores de reposo previamente verificados; no cambia direcciones.
        for n, value in ((464, '1'), (463, '0'), (461, '0')):
            Path('/sys/class/gpio/gpio%d/value' % n).write_text(value)
    time.sleep(1)
PY
```

Para contrastar el maestro Python usar `['python3','-B','spi_master.py','2']`
en subprocess.run. No volcar stdout binario directamente a UART. El tiempo de
subproceso incluye costes distintos del tiempo interno reportado por C.

Correcto exige SC, 264 bytes, CRC válido, estado cero, muestras dentro de rango y
dos transferencias consecutivas coherentes; revisar avance de secuencia y contenido
con entradas conocidas antes de declarar adquisición validada. Ceros, `53` repetido,
cabecera aislada, exit 0 o compilación no bastan.

## 6. Corrección local y recuperación del estado anterior

Compilar la rama con `pio run -d firmware/stm32/spi_polling -e nucleo_l432kc`.
Comprobar con nm que SysTick_Handler es fuerte y distinto de Default_Handler;
objdump debe mostrar la llamada/salto a HAL_IncTick. La corrección está en un
archivo separado, sin tocar ADC ni protocolo. El diff y el commit permiten retirarla
mediante un commit inverso revisado; no reset/clean ni restauración indiscriminada.

**No programar todavía:** falta la fuente de la iteración instalada o una decisión
explícita sobre la versión que puede sustituirla. Respaldo Flash disponible fuera
de Git y hash en el diagnóstico SPI. Restaurarlo implicaría escribir Flash y
reiniciar STM32: verificar identidad, hash y autorización de esa operación primero.
No incluye option bytes. No restaurar la microSD ni reiniciar Milk-V.

La tarea conservó fuentes/binario remoto y servicio inactive, con CS alto y
CLK/MOSI bajos. Las aperturas UART se cerraron. Para retirar el acceso SSH temporal
desde Windows después de salir de la VM:

```powershell
& 'C:\Program Files\VBoxManage.exe' controlvm vmmm natpf1 delete milkv-debug-ssh
```

La VM puede conservar el USB-UART para usar su consola. Si Andrew decide devolverlo
a Windows, cerrar antes todos los terminales y ejecutar `controlvm vmmm usbdetach`
con el UUID vigente verificado. No apagar/reiniciar la Milk-V para esa operación.
No usar el UUID del ST-LINK. El error de COM11 en Windows podría reaparecer.
