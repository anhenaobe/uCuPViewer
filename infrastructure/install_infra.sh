#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
readonly WEB_ROOT="/var/www/ucupviewer"
readonly APP_ROOT="/opt/ucupviewer"
readonly SERVICE_USER="ucupviewer"
readonly NGINX_AVAILABLE="/etc/nginx/sites-available"
readonly NGINX_ENABLED="/etc/nginx/sites-enabled"
readonly NGINX_SITE="${NGINX_AVAILABLE}/ucupviewer.conf"
readonly SYSTEMD_UNIT="/etc/systemd/system/ucupviewer-backend.service"

log() { printf '[ucupviewer] %s\n' "$*"; }
die() { printf '[ucupviewer] ERROR: %s\n' "$*" >&2; exit 1; }

[[ "$(id -u)" -eq 0 ]] || die "Run with sudo on the Raspberry Pi."
[[ -f "${SCRIPT_DIR}/nginx_ucupviewer.conf" ]] || die "Nginx template not found beside this script."
[[ -f "${SCRIPT_DIR}/ucupviewer-backend.service" ]] || die "systemd unit template not found beside this script."
[[ -f "${SCRIPT_DIR}/spi_protocol.py" ]] || die "SPI protocol module not found beside this script."

if [[ -r /proc/device-tree/model ]]; then
    pi_model="$(tr -d '\0' </proc/device-tree/model)"
    [[ "$pi_model" == *"Raspberry Pi 4"* ]] || die "Expected Raspberry Pi 4 Model B, found: ${pi_model}"
else
    die "Cannot identify Raspberry Pi model from /proc/device-tree/model."
fi

if [[ -f /boot/firmware/config.txt ]]; then
    boot_config=/boot/firmware/config.txt
elif [[ -f /boot/config.txt ]]; then
    boot_config=/boot/config.txt
else
    die "Could not find Raspberry Pi boot config at /boot/firmware/config.txt or /boot/config.txt."
fi

if [[ -L /etc/nginx/sites-enabled/default ]]; then
    default_target="$(readlink -f -- /etc/nginx/sites-enabled/default || true)"
    [[ "$default_target" == /etc/nginx/sites-available/default ]] \
        || die "A custom Nginx default-site link exists; review it manually before installing."
elif [[ -e /etc/nginx/sites-enabled/default ]]; then
    die "A non-symlink Nginx default site exists; review it manually before installing."
fi

backend_port="${UCUPVIEWER_BACKEND_PORT:-5000}"
[[ "$backend_port" =~ ^[0-9]{1,5}$ ]] || die "UCUPVIEWER_BACKEND_PORT must be an integer from 1 to 65535."
backend_port=$((10#$backend_port))
(( backend_port >= 1 && backend_port <= 65535 )) || die "UCUPVIEWER_BACKEND_PORT must be an integer from 1 to 65535."

log "Installing Nginx and Python spidev package."
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y nginx python3-spidev

log "Enabling SPI in ${boot_config} (a reboot may be required)."
backup="${boot_config}.ucupviewer.$(date +%Y%m%d%H%M%S).bak"
cp -a -- "$boot_config" "$backup"
python3 - "$boot_config" <<'PY'
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
lines = text.splitlines()
updated = []
for line in lines:
    if re.match(r"^\s*dtparam\s*=\s*spi\s*=", line) and not line.lstrip().startswith("#"):
        updated.append("# superseded by global uCuPViewer setting: " + line)
    else:
        updated.append(line)

# Place one global setting before conditional [section] blocks.
section_index = next(
    (i for i, line in enumerate(updated) if re.match(r"^\s*\[", line)),
    len(updated),
)
updated.insert(section_index, "dtparam=spi=on")

path.write_text("\n".join(updated).rstrip() + "\n", encoding="utf-8")
PY

if ! getent group "$SERVICE_USER" >/dev/null; then
    groupadd --system "$SERVICE_USER"
fi
if ! getent passwd "$SERVICE_USER" >/dev/null; then
    useradd --system --no-create-home --home-dir "$APP_ROOT" \
        --shell /usr/sbin/nologin --gid "$SERVICE_USER" "$SERVICE_USER"
fi

for group in spi gpio; do
    if getent group "$group" >/dev/null; then
        usermod -a -G "$group" "$SERVICE_USER"
        log "Added ${SERVICE_USER} to existing ${group} group."
    else
        log "Group ${group} is absent on this OS; no group was created. Check device-node permissions with the Pi administrator."
    fi
done

install -d -o root -g root -m 0755 "$APP_ROOT"
install -d -o root -g "$SERVICE_USER" -m 0750 "${APP_ROOT}/backend"
if [[ -d "${REPO_ROOT}/backend" ]]; then
    cp -a -- "${REPO_ROOT}/backend/." "${APP_ROOT}/backend/"
fi
install -m 0640 "${SCRIPT_DIR}/spi_protocol.py" "${APP_ROOT}/backend/spi_protocol.py"
chown -R root:"$SERVICE_USER" "${APP_ROOT}/backend"
find "${APP_ROOT}/backend" -type d -exec chmod 0750 {} +
find "${APP_ROOT}/backend" -type f -exec chmod 0640 {} +

install -d -o root -g root -m 0755 "$WEB_ROOT"
if [[ -d "${REPO_ROOT}/frontend" ]]; then
    install -d -o root -g root -m 0755 "${WEB_ROOT}/frontend"
    cp -a -- "${REPO_ROOT}/frontend/." "${WEB_ROOT}/frontend/"
fi
chown -R root:www-data "$WEB_ROOT"
find "$WEB_ROOT" -type d -exec chmod 0755 {} +
find "$WEB_ROOT" -type f -exec chmod 0644 {} +

install -d -o root -g root -m 0755 "$NGINX_AVAILABLE" "$NGINX_ENABLED"
install -d -o root -g root -m 0755 /etc/systemd/system
timestamp="$(date +%Y%m%d%H%M%S)"
if [[ -e "$NGINX_SITE" ]]; then
    cp -a -- "$NGINX_SITE" "${NGINX_SITE}.backup.${timestamp}"
fi
if [[ -e "${NGINX_ENABLED}/ucupviewer.conf" || -L "${NGINX_ENABLED}/ucupviewer.conf" ]]; then
    cp -a -- "${NGINX_ENABLED}/ucupviewer.conf" \
        "${NGINX_ENABLED}/ucupviewer.conf.backup.${timestamp}"
fi
sed "s/127\.0\.0\.1:5000/127.0.0.1:${backend_port}/" \
    "${SCRIPT_DIR}/nginx_ucupviewer.conf" >"${NGINX_SITE}.tmp"
chmod 0644 "${NGINX_SITE}.tmp"
mv -f -- "${NGINX_SITE}.tmp" "$NGINX_SITE"
ln -sfn -- "$NGINX_SITE" "${NGINX_ENABLED}/ucupviewer.conf"

# Disable only the packaged default-site link, preserving a timestamped backup.
if [[ -L "${NGINX_ENABLED}/default" ]]; then
    default_target="$(readlink -f -- "${NGINX_ENABLED}/default" || true)"
    if [[ "$default_target" == /etc/nginx/sites-available/default ]]; then
        default_backup="${NGINX_AVAILABLE}/default.disabled-by-ucupviewer.$(date +%Y%m%d%H%M%S)"
        cp -a -- "${NGINX_ENABLED}/default" "$default_backup"
        rm -- "${NGINX_ENABLED}/default"
        log "Disabled the packaged Nginx default-site link; backup: ${default_backup}"
    else
        die "A custom Nginx default-site link exists at ${NGINX_ENABLED}/default; review it manually before enabling this site."
    fi
elif [[ -e "${NGINX_ENABLED}/default" ]]; then
    die "A non-symlink Nginx default site exists at ${NGINX_ENABLED}/default; review it manually."
fi

if [[ -e "$SYSTEMD_UNIT" ]]; then
    cp -a -- "$SYSTEMD_UNIT" "${SYSTEMD_UNIT}.backup.${timestamp}"
fi
sed "s/UCUPVIEWER_BACKEND_PORT=5000/UCUPVIEWER_BACKEND_PORT=${backend_port}/" \
    "${SCRIPT_DIR}/ucupviewer-backend.service" >"${SYSTEMD_UNIT}.tmp"
chmod 0644 "${SYSTEMD_UNIT}.tmp"
mv -f -- "${SYSTEMD_UNIT}.tmp" "$SYSTEMD_UNIT"
install -d -o root -g root -m 0750 /etc/ucupviewer

nginx -t
systemctl enable nginx
systemctl restart nginx

systemctl daemon-reload
if [[ -f "${APP_ROOT}/backend/main.py" ]]; then
    systemctl enable --now ucupviewer-backend.service
    log "Backend service enabled and started."
else
    log "Backend unit installed but not enabled: backend/main.py is not present yet. Coordinate the entry point with Pipe, then rerun this installer."
fi

if [[ ! -f "${WEB_ROOT}/frontend/index.html" ]]; then
    log "No frontend/index.html was found; Nginx is installed, but the dashboard is not deployable yet. Coordinate frontend build output with Mateo."
fi

log "SPI boot configuration updated. Reboot the Pi, then verify /dev/spidev* and the service user's effective permissions."
log "Backend port configured for Nginx: ${backend_port} (coordinate with Pipe before use)."
log "Check services with: systemctl status nginx ucupviewer-backend; journalctl -u ucupviewer-backend -b"
