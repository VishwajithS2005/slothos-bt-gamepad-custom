#!/usr/bin/env bash
# install_xbox.sh — Deploy isolated Xbox Mode alongside standard BT Mode.

set -euo pipefail

# ---------- helpers ----------
c_red()   { printf '\033[31m%s\033[0m\n' "$*"; }
c_grn()   { printf '\033[32m%s\033[0m\n' "$*"; }
c_blu()   { printf '\033[34m%s\033[0m\n' "$*"; }
log()     { printf '[*] %s\n' "$*"; }
log_ok()  { printf '[\033[32m✓\033[0m] %s\n' "$*"; }
log_err() { printf '[\033[31m✗\033[0m] %s\n' "$*" >&2; }
log_die() { log_err "$*"; exit 1; }

# ---------- arg parsing ----------
MODE="install"
PASSWORD=""
DEVICE=""
SSH_USER="root"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --uninstall) MODE="uninstall"; shift ;;
    --password)
      if [[ $# -ge 2 && "${2:-}" != -* ]]; then PASSWORD="$2"; shift 2; else PASSWORD="root"; shift; fi ;;
    --password=*) PASSWORD="${1#*=}"; shift ;;
    -h|--help) exit 0 ;;
    *) if [[ -z "$DEVICE" ]]; then DEVICE="$1"; shift; else SSH_USER="$1"; shift; fi ;;
  esac
done

[[ -n "$DEVICE" ]] || log_die "Usage: $0 [--uninstall] [--password [PW]] <device-ip> [ssh-user]"

# ---------- ssh / scp wrappers ----------
SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10)
SSH_WRAPPER=()
if [[ -n "$PASSWORD" ]]; then SSH_WRAPPER=(sshpass -p "$PASSWORD"); fi
SSH=("${SSH_WRAPPER[@]}" ssh "${SSH_OPTS[@]}")
SCP=("${SSH_WRAPPER[@]}" scp "${SSH_OPTS[@]}")

# ---------- ISOLATED PATHS ----------
HERE="$(cd "$(dirname "$0")" && pwd)"
REMOTE_DIR="/usr/local/slothos/bt_gamepad_xbox"
BT_MODE_DIR="/usr/local/slothos/bt_mode_xbox"
SERVICE_SRC="${HERE}/bt_gamepad_xbox.service"
SERVICE_DST="/etc/systemd/system/bt_gamepad_xbox.service"
DROPIN_SRC="${HERE}/bluetooth.service.d/exec.conf"
DROPIN_DST="/etc/systemd/system/bluetooth.service.d/exec.conf"
BT_MODE_LAUNCH_DST="/usr/local/bin/slothos-bt-mode-xbox"

"${SSH[@]}" "${SSH_USER}@${DEVICE}" 'echo ok' >/dev/null 2>&1 || log_die "SSH to ${DEVICE} failed."

# =====================================================================
# UNINSTALL (ISOLATED)
# =====================================================================
if [[ "$MODE" == "uninstall" ]]; then
  log "Stopping + disabling bt_gamepad_xbox…"
  "${SSH[@]}" "${SSH_USER}@${DEVICE}" '
    systemctl stop bt_gamepad_xbox 2>/dev/null || true
    systemctl disable bt_gamepad_xbox 2>/dev/null || true
    rm -f /etc/systemd/system/bt_gamepad_xbox.service
    systemctl daemon-reload
    rm -rf '"${REMOTE_DIR}"'
    rm -rf '"${BT_MODE_DIR}"'
    rm -f '"${BT_MODE_LAUNCH_DST}"'
    rm -f /mnt/mmc/Roms/APPS/BT_Mode_Xbox.sh /mnt/mmc/Roms/APPS/Imgs/BT_Mode_Xbox.png
    rm -rf /mnt/mmc/Roms/APPS/bt_mode_xbox
    rm -f /mnt/sdcard/Roms/APPS/BT_Mode_Xbox.sh /mnt/sdcard/Roms/APPS/Imgs/BT_Mode_Xbox.png
    rm -rf /mnt/sdcard/Roms/APPS/bt_mode_xbox
  ' || log_die "Uninstall commands failed."
  log_ok "Xbox Mode uninstalled cleanly (Standard version untouched)."
  exit 0
fi

# =====================================================================
# INSTALL (ISOLATED)
# =====================================================================
"${SSH[@]}" "${SSH_USER}@${DEVICE}" 'chmod 755 /root' || true
HOST_TIME=$(date -u '+%Y-%m-%d %H:%M:%S')
"${SSH[@]}" "${SSH_USER}@${DEVICE}" "date -s '${HOST_TIME}' >/dev/null || true; hwclock --systohc 2>/dev/null || true" || true

log "Copying Xbox stack to ${REMOTE_DIR}/…"
"${SSH[@]}" "${SSH_USER}@${DEVICE}" "mkdir -p ${REMOTE_DIR}"
"${SCP[@]}" -q "${HERE}"/{main.py,bt_l2cap_v2.py,BluezProfile.py,BluezAgent.py,hid_descriptor.py,evdev_to_hid.py,evdev_reader.py,sdp_record_gamepad.xml,sdp_record_pnp.xml,set_did.py,requirements.txt} "${SSH_USER}@${DEVICE}:${REMOTE_DIR}/" || log_die "scp of stack failed."

# INJECT XBOX VID/PID ON THE FLY
log "Spoofing Xbox Wireless Controller VID/PID in SDP records..."
"${SSH[@]}" "${SSH_USER}@${DEVICE}" "sed -i 's/0x1209/0x045E/g; s/0x5017/0x02FD/g' ${REMOTE_DIR}/sdp_record_pnp.xml"

log "Installing systemd units…"
"${SSH[@]}" "${SSH_USER}@${DEVICE}" "mkdir -p /etc/systemd/system/bluetooth.service.d"
"${SCP[@]}" -q "$SERVICE_SRC" "${SSH_USER}@${DEVICE}:${SERVICE_DST}"
"${SCP[@]}" -q "$DROPIN_SRC" "${SSH_USER}@${DEVICE}:${DROPIN_DST}"
"${SSH[@]}" "${SSH_USER}@${DEVICE}" 'systemctl daemon-reload; systemctl restart bluetooth; sleep 3'

log "Enabling + starting bt_gamepad_xbox…"
"${SSH[@]}" "${SSH_USER}@${DEVICE}" '
  hciconfig hci0 up 2>/dev/null || true
  hciconfig hci0 auth
  systemctl enable bt_gamepad_xbox
  systemctl restart bt_gamepad_xbox
  sleep 2
' || log_die "bt_gamepad_xbox failed to start."

log "Deploying Xbox Splash App…"
SPLASH_SRC="${HERE}/app/splash.png"
if [[ -f "$SPLASH_SRC" ]]; then
  "${SSH[@]}" "${SSH_USER}@${DEVICE}" "mkdir -p ${BT_MODE_DIR}"
  "${SCP[@]}" -q "${HERE}/app/bt_mode_xbox.py" "${HERE}/app/requirements.txt" "${SPLASH_SRC}" "${SSH_USER}@${DEVICE}:${BT_MODE_DIR}/"
fi

log "Auto-creating BT_Mode_Xbox launcher entry…"
ICON_SRC="${HERE}/app/icon.png"
"${SSH[@]}" "${SSH_USER}@${DEVICE}" '
  mkdir -p /mnt/mmc/Roms/APPS/bt_mode_xbox /mnt/mmc/Roms/APPS/Imgs
  cat > /mnt/mmc/Roms/APPS/BT_Mode_Xbox.sh <<"ENTRY"
#!/bin/bash
progdir="$(cd $(dirname "$0") || exit; pwd)"/bt_mode_xbox
python3 ${progdir}/main.py > "${progdir}/log.txt" 2>&1
ENTRY
  chmod 755 /mnt/mmc/Roms/APPS/BT_Mode_Xbox.sh
  cat > /mnt/mmc/Roms/APPS/bt_mode_xbox/main.py <<"PYSTUB"
import runpy
runpy.run_path("/usr/local/slothos/bt_mode_xbox/bt_mode_xbox.py", run_name="__main__")
PYSTUB
  chmod 755 /mnt/mmc/Roms/APPS/bt_mode_xbox/main.py
  if pgrep dmenu.bin >/dev/null 2>&1; then killall -s USR1 dmenu.bin 2>/dev/null || true; fi
' || true

if [[ -f "$ICON_SRC" ]]; then
  "${SCP[@]}" -q "$ICON_SRC" "${SSH_USER}@${DEVICE}:/mnt/mmc/Roms/APPS/Imgs/BT_Mode_Xbox.png" 2>/dev/null || true
  "${SSH[@]}" "${SSH_USER}@${DEVICE}" '
    if mountpoint -q /mnt/sdcard 2>/dev/null; then
      mkdir -p /mnt/sdcard/Roms/APPS/bt_mode_xbox /mnt/sdcard/Roms/APPS/Imgs
      cp -f /mnt/mmc/Roms/APPS/BT_Mode_Xbox.sh /mnt/sdcard/Roms/APPS/BT_Mode_Xbox.sh 2>/dev/null || true
      cp -f /mnt/mmc/Roms/APPS/bt_mode_xbox/main.py /mnt/sdcard/Roms/APPS/bt_mode_xbox/main.py 2>/dev/null || true
      cp -f /mnt/mmc/Roms/APPS/Imgs/BT_Mode_Xbox.png /mnt/sdcard/Roms/APPS/Imgs/BT_Mode_Xbox.png 2>/dev/null || true
      chmod 755 /mnt/sdcard/Roms/APPS/BT_Mode_Xbox.sh /mnt/sdcard/Roms/APPS/bt_mode_xbox/main.py 2>/dev/null || true
    fi
  ' || true
fi

DEVICE_BDADDR=$("${SSH[@]}" "${SSH_USER}@${DEVICE}" 'hcitool dev | tail -n +2 | awk "{print \$2}" | head -1')
echo
c_grn "=== Xbox Mode Installed ==="
echo "You can now safely run both versions. To switch profiles:"
echo "1. Press Start+Select to close the currently running app on your handheld."
echo "2. Open the other mode in your APPS menu."
echo "3. Connect to the respective device on your Android/PC Bluetooth settings."