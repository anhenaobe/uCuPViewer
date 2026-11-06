#!/bin/sh
set -eu
cd /root/osciloscopio_final/milkv
chmod +x preparar_gpio.sh compilar.sh
if command -v gcc >/dev/null 2>&1; then
    ./compilar.sh
else
    echo 'AVISO: gcc ausente. Usando respaldo Python SPI, sin compilación C.'
fi
./preparar_gpio.sh
install -m 644 osciloscopio.service /etc/systemd/system/osciloscopio.service
systemctl daemon-reload
systemctl enable --now osciloscopio.service
if ! command -v nginx >/dev/null 2>&1; then
  echo 'AVISO: Nginx no instalado. Instálalo cuando haya conectividad: apt-get update && apt-get install -y nginx'
  echo 'Mientras tanto usa HTTP directo en la Milk-V: python3 app.py --host 0.0.0.0 --port 8080'
else
  mkdir -p /etc/nginx/conf.d
  cp nginx_osciloscopio.conf /etc/nginx/conf.d/osciloscopio.conf
  # Evita conflicto de varios default_server en Debian.
  if [ -L /etc/nginx/sites-enabled/default ]; then
      rm /etc/nginx/sites-enabled/default
  fi
  nginx -t
  systemctl enable nginx
  systemctl restart nginx
  echo 'Nginx sirve dashboard desde Milk-V por HTTP puerto 80.'
fi
systemctl --no-pager status osciloscopio.service | head -20
