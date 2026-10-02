#!/usr/bin/env python3
"""SlothOS Controller — Xbox Bluetooth Mode splash."""
import os, sys, struct, subprocess, time, mmap
from fcntl import ioctl
import evdev
from PIL import Image, ImageDraw, ImageFont

# ISOLATED PATHS
SPLASH_PATH = "/usr/local/slothos/bt_mode_xbox/splash.png"
SERVICE = "bt_gamepad_xbox"

INPUT_DEV = "/dev/input/event1"
FB_DEV = "/dev/fb0"
PANEL_W, PANEL_H = 640, 480
ERROR_HOLD_SEC = 5

CODE_START = 311
CODE_SELECT = 310

FBIOGET_VSCREENINFO = 0x4600
FBIOPUT_VSCREENINFO = 0x4601
FBIOBLANK = 0x4611
VSCREENINFO_SIZE = 160

FB_VINFO_RG35XXH = bytes.fromhex(
    "80020000" "e0010000" "80020000" "c0030000"
    "00000000" "00000000" "20000000" "00000000"
    "08000000" "08000000" "00000000"
    "08000000" "08000000" "00000000"
    "08000000" "08000000" "00000000"
    "08000000" "08000000" "00000000"
    "00000000" "00000000" "00000000" "00000000"
    "00000000" "c2a20000" "1a000000" "54000000"
    "0b000000" "1b000000" "14000000" "04000000"
    "00000000" "00000000" "00000000" "00000000"
)
FB_VINFO_RG35XXH = FB_VINFO_RG35XXH.ljust(VSCREENINFO_SIZE, b"\x00")
FONT_PATH = "/usr/share/fonts/TTF/DejaVuSansMono.ttf"

class Framebuffer:
    def __init__(self):
        self.fd = -1
        self.mm = None
        self.saved_vinfo = None

    def open(self):
        self.fd = os.open(FB_DEV, os.O_RDWR)
        buf = bytearray(VSCREENINFO_SIZE)
        try:
            ioctl(self.fd, FBIOGET_VSCREENINFO, buf)
            self.saved_vinfo = bytes(buf)
        except OSError:
            self.saved_vinfo = None
        try: ioctl(self.fd, FBIOPUT_VSCREENINFO, bytearray(FB_VINFO_RG35XXH))
        except OSError: pass
        try: ioctl(self.fd, FBIOBLANK, 0)
        except OSError: pass
        self.mm = mmap.mmap(self.fd, PANEL_W * PANEL_H * 4)

    def write_image(self, img):
        if img.size != (PANEL_W, PANEL_H): img = img.resize((PANEL_W, PANEL_H), Image.LANCZOS)
        if img.mode != "RGBA": img = img.convert("RGBA")
        self.mm.seek(0)
        self.mm.write(img.tobytes())

    def close(self):
        if self.mm:
            try: self.mm.close()
            except Exception: pass
        if self.fd >= 0:
            if self.saved_vinfo:
                try: ioctl(self.fd, FBIOPUT_VSCREENINFO, bytearray(self.saved_vinfo))
                except OSError: pass
            try: os.close(self.fd)
            except Exception: pass

def render_error(fb, msg):
    img = Image.new("RGBA", (PANEL_W, PANEL_H), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, PANEL_H // 2 - 30, PANEL_W, PANEL_H // 2 + 30], fill=(180, 30, 30))
    try: font = ImageFont.truetype(FONT_PATH, 28)
    except OSError: font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), msg, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((PANEL_W - tw) // 2 - bbox[0], (PANEL_H - th) // 2 - bbox[1]), msg, fill=(255, 255, 255), font=font)
    fb.write_image(img)

def render_splash(fb):
    img = Image.open(SPLASH_PATH).convert("RGBA")
    fb.write_image(img)

def service_is_active():
    return subprocess.run(["systemctl", "is-active", "--quiet", SERVICE]).returncode == 0

def combo_pressed(dev):
    sh, sl = False, False
    try:
        for event in dev.read():
            if event.type == evdev.ecodes.EV_KEY:
                if event.code == CODE_START: sh = bool(event.value)
                elif event.code == CODE_SELECT: sl = bool(event.value)
                if sh and sl: return True
    except BlockingIOError: pass
    return False

def main():
    subprocess.run(["systemctl", "start", SERVICE], check=False)
    time.sleep(1)
    service_ok = service_is_active()

    fb = Framebuffer()
    try: fb.open()
    except OSError: fb = None

    if fb:
        try:
            if service_ok: render_splash(fb)
            else: render_error(fb, "Xbox BT service failed to start")
        except Exception: pass

    if not service_ok:
        sys.stderr.write(f"bt_gamepad_xbox failed to start; exiting in {ERROR_HOLD_SEC}s\n")
        try: err_dev = evdev.InputDevice(INPUT_DEV)
        except OSError: err_dev = None
        deadline = time.monotonic() + ERROR_HOLD_SEC
        while time.monotonic() < deadline:
            if err_dev and combo_pressed(err_dev): break
            time.sleep(0.05)
        if err_dev: err_dev.close()
        subprocess.run(["systemctl", "stop", SERVICE], check=False)
        if fb: fb.close()
        sys.exit(1)

    try: dev = evdev.InputDevice(INPUT_DEV)
    except OSError:
        subprocess.run(["systemctl", "stop", SERVICE], check=False)
        if fb: fb.close()
        sys.exit(1)

    sh, sl = False, False
    try:
        for event in dev.read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                if event.code == CODE_START: sh = bool(event.value)
                elif event.code == CODE_SELECT: sl = bool(event.value)
                if sh and sl: break
    finally:
        subprocess.run(["systemctl", "stop", SERVICE], check=False)
        if fb: fb.close()
    sys.exit(0)

if __name__ == "__main__":
    main()