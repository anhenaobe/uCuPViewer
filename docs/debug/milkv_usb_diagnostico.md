# Acceso USB a Milk-V Duo S — 5 de noviembre de 2026

## Resultado

**Acceso recuperado:** Windows → SSH local a VM Debian `vmmm` → adaptador
Prolific USB-UART → consola `root@duos` de la Milk-V. No se reinstaló ningún
sistema, no se cambió el controlador Windows y no se reinició la Milk-V.
Andrew confirmó que ese adaptador está conectado a la Milk-V y autorizó arrancar
`vmmm` y asignarle exclusivamente el USB-UART. Las credenciales no se guardan aquí.

## Entornos distinguidos

| Sistema | Evidencia |
|---|---|
| Ejecutor Codex | Windows NT 10.0.26200.0, PowerShell, equipo ANDREW, Lenovo 83LK |
| VM autorizada | VirtualBox 7.2.16, `vmmm`, Debian 13; `uname`: Linux vmmm 6.12.107+deb13-amd64, x86_64 |
| Milk-V real | `uname`: Linux duos 5.10.4-20240527-2+, riscv64; `/etc/os-release`: Debian GNU/Linux forky/sid |

El Debian empleado anteriormente por Andrew está en otro computador, según su
confirmación. Windows tiene HypervisorPresent=true; eso solo no permite deducir
que Codex corre dentro de una VM. La VM `vmmm` estaba apagada y se inició para
esta sesión. La otra VM registrada, ubicada en D:, figuraba inaccesible.
WSL no está instalado. `uname`, `lsusb` e `ip` no estaban disponibles como comandos
del anfitrión Windows; se ejecutaron después **dentro de Debian VM**.

Proyecto accesible: worktree `C:\dev\7mo\Linux\milk-review-20261105`, rama
`debug/milkv-usb-access`, desde `81c0645`. La copia original del proyecto y su ZIP
se conservaron. No se trabajó sobre main.

## Enumeración y fallo inicial de Windows

| Dispositivo | Identificación | Resultado |
|---|---|---|
| USB-UART Prolific | VID 067B, PID 2303; instancia `USB\VID_067B&PID_2303\5&2B1BFFB5&0&13`; COM11 | Detectado, pero no abría |
| ST-LINK | VID 0483, PID 374B; serie `0672FF373146363143221241`; COM9 | Distinto dispositivo: depurador y VCP de STM32 |
| Bluetooth | COM3 y COM4 | No usados como consola Milk-V |
| Cámara y Bluetooth Intel | VID/PID 13D3:54B6 y 8087:0026 | No relacionados con el acceso UART |

Prolific se anunciaba como `PL2303HXA PHASED OUT SINCE 2012. PLEASE CONTACT YOUR
SUPPLIER.`. Driver `ser2pl_1`, versión 3.9.6.0, PnP ProblemCode=0. El registro
SerialComm y PySerial enumeraban COM11; Win32_SerialPort no lo listaba.
El log System registra instalación del driver Prolific 3.9.6.0 a las 19:30 del
5 de noviembre. La coincidencia temporal no demuestra por sí sola causalidad.

Dos aperturas independientes, .NET SerialPort y PySerial, a 115200/8N1, sin flujo,
DTR/RTS desactivados, fallaron **antes de enviar o recibir datos**:

```text
A device which does not exist was specified.
SerialException ... OSError(22, 'A device which does not exist was specified.', None, 433)
```

No era una consola silenciosa: fallaba la apertura del puerto. No hubo error
AccessDenied ni prueba de que Minicom lo tuviera abierto. No aparecieron procesos
Minicom/PuTTY/TeraTerm en la consulta; ello no descarta todos los posibles dueños.
VirtualBox mostraba `Busy`, que tampoco identifica un proceso propietario.
El posterior éxito Linux con el mismo adaptador apunta al acceso/driver Windows,
sin demostrar el motivo interno exacto de ese fallo.

No se detectó interfaz CDC-NCM/RNDIS de Milk-V: red Windows con Wi-Fi, Ethernet
desconectado y adaptador VirtualBox host-only. Este último no es un USB Gadget.
La conexión confirmada es USB-UART; no se deduce nada sobre la configuración
USB-C de la imagen de Milk-V a partir de esa ausencia.

## Recuperación mediante VM

`VBoxManage.exe` está en `C:\Program Files\VBoxManage.exe`, no en el subdirectorio
Oracle habitual. Se ejecutó `list vms`, `list runningvms`, `list usbhost` y
`showvminfo vmmm`. Se inició con `startvm vmmm --type headless` y se conectó el
Prolific con `controlvm vmmm usbattach <UUID vigente>`. El primer UUID había
cambiado al arrancar: se reenumeró por VID/PID antes de reintentar. La comprobación
final mostró exclusivamente el Prolific capturado; ST-LINK permaneció en Windows.

En Debian VM:

```text
Bus 002 Device 003: ID 067b:2303 Prolific Technology, Inc. PL2303 Serial Port / Mobile Phone Data Cable
crw-rw---- root dialout 188,0 /dev/ttyUSB0
/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller-if00-port0 -> ../../ttyUSB0
```

`vboxuser` pertenece a sudo, pero no a dialout. `sudo fuser -v /dev/ttyUSB0` no
mostró usuarios del dispositivo. Se usó sudo puntual, no chmod ni cambios de grupos.
La VM no tenía PySerial, Minicom o picocom; se usó Python estándar con termios,
115200, CS8, CLOCAL, CREAD, sin paridad/flujo, exclusión TIOCEXCL y lectura acotada.
Cada apertura restauró termios y cerró el descriptor. La escucha pasiva de 8 s
no recibió bytes; un único CR produjo:

```text
root@duos:~/osciloscopio_final/milkv#
```

Se verificó el prompt con `uname -a`, `/etc/os-release` y `pwd`; no era U-Boot.
No se enviaron comandos de arranque. Para obtener salida legible de la VM se usó
SSH existente con una redirección temporal NAT `milkv-debug-ssh`, limitada a
`127.0.0.1:22222` del anfitrión → puerto 22 de la VM. La huella ED25519 se comparó
con `/etc/ssh/ssh_host_ed25519_key.pub` leído en consola antes de aceptarla.

## Comprobaciones dentro de la Milk-V

- `/root/osciloscopio_final/milkv` contiene los maestros C/Python, protocolo,
  app, preparación GPIO, configuración del servicio y binario RISC-V.
- Raíz `/dev/mmcblk0p2`, ext4 `rw,relatime`; 29 GiB, 4,9 GiB usados, 23 GiB
  disponibles. Esto no es una comprobación exhaustiva de integridad del filesystem.
- `osciloscopio.service`: enabled pero **inactive (dead)** al llegar, terminación
  SIGTERM; no se inició ni detuvo en esta tarea. Logs recientes: cabecera cero.
- No se encontraron procesos app.py, spi_master o milkv_stream en la consulta.
- GCC 16.2.0-1 Debian, Python 3.14.7, cvi_pinmux disponibles.
- `/proc/config.gz`: `# CONFIG_SPI is not set`; no `/dev/spidev*`.
- La hora Milk-V indicaba 2026-08-28 y el anfitrión 2026-11-05; no se corrigió.
  No ordenar versiones ni correlacionar relojes por esas fechas sin más evidencia.
- GPIO, pinmux, firmware y pruebas: [diagnóstico SPI](milkv_spi_diagnostico.md).

## Comandos de diagnóstico utilizados

Windows: `[Environment]::OSVersion.VersionString`, `Get-CimInstance` para sistema,
puertos y driver, `Get-PnpDevice -PresentOnly`, `Get-PnpDeviceProperty`, registro
`HKLM:\HARDWARE\DEVICEMAP\SERIALCOMM`, `Get-NetAdapter`, `Get-NetIPAddress`,
`Get-Process`, `Get-WinEvent` System, `wsl --list --running`; SerialPort.Open y
PySerial.open sobre COM11. VirtualBox: list/showvminfo/startvm/controlvm descritos.

Debian VM: `uname -a`, `lsusb`, `ls -l /dev/ttyUSB* /dev/ttyACM* /dev/serial/by-id/`,
`ip -br link`, `id`, `sudo fuser -v /dev/ttyUSB0`, `sudo dmesg | tail -20`,
`systemctl is-active ssh`. Milk-V: `uname -a`, `cat /etc/os-release`, `pwd`,
`findmnt`, `df -h /`, `systemctl status/cat osciloscopio.service`, `ps`, `find`,
`nl -ba`, `sha256sum`, lecturas sysfs y `cvi_pinmux -r`.

No hace falta desconectar cables para recuperar acceso: la vía UART por VM quedó
demostrada. Ver [procedimiento](milkv_procedimiento_recuperacion.md) para repetirla
y retirar la redirección temporal sin afectar la Milk-V.

Estado al cerrar la sesión: sondeos UART terminados, fuser sin propietario,
sesiones de VM cerradas y redirección `milkv-debug-ssh` eliminada. `vmmm` continúa
running con el Prolific asignado; ST-LINK sigue en Windows. No se apagó la VM ni
se devolvió el adaptador al driver COM11 que había fallado.
