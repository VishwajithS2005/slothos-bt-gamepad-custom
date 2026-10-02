"""evdev event code -> HID report field mapping for the ANBERNIC RG35XX H."""

import evdev.ecodes as e

# Android natively reads HID Buttons sequentially using the standard Linux Gamepad layout.
# It expects: 1=A, 2=B, 3=C, 4=X, 5=Y, 6=Z, 7=L1, 8=R1, 9=L2, 10=R2, 11=Select, 12=Start, 13=Mode, 14=L3, 15=R3.
# We must skip 3 (C) and 6 (Z) so everything lands on the exact expected buttons for Minecraft.

BUTTON_MAP = {
    304: 1,   # A      -> HID 1  (Android A)
    305: 2,   # B      -> HID 2  (Android B)
              # Skip 3 (Android C - Ignored by Minecraft)
    307: 4,   # X      -> HID 4  (Android X)
    306: 5,   # Y      -> HID 5  (Android Y)
              # Skip 6 (Android Z - Ignored by Minecraft)
    308: 7,   # L1     -> HID 7  (Android L1 / LB)
    309: 8,   # R1     -> HID 8  (Android R1 / RB)
    314: 9,   # L2     -> HID 9  (Android L2 / LT - Places items)
    315: 10,  # R2     -> HID 10 (Android R2 / RT - Destroys items)
    310: 11,  # Select -> HID 11 (Android Select / View)
    311: 12,  # Start  -> HID 12 (Android Start / Menu)
    312: 13,  # Func   -> HID 13 (Android Mode / Xbox Logo)
    313: 14,  # L3     -> HID 14 (Android L3 / LSB)
    316: 15,  # R3     -> HID 15 (Android R3 / RSB)
}

# Since we mapped L2 and R2 directly to HID Buttons 9 and 10, 
# we no longer need to spoof them as Analog Axes for Android.
# Leaving this dict empty safely bypasses the axis spoofing in main.py.
TRIGGER_BUTTON_AXES = {}

# The sticks are perfect as confirmed
AXIS_MAP = {
    2: 0,   # Left Analog X -> HID X (offset 0)
    3: 1,   # Left Analog Y -> HID Y (offset 1)
    4: 2,   # Right Analog X -> HID Z (offset 2)
    5: 3,   # Right Analog Y -> HID Rz (offset 3)
}

AXIS_ALIASES = {}

# ---------------------------------------------------------------- D-pad
DPAD_AXIS_X = 16  # ABS_HAT0X
DPAD_AXIS_Y = 17  # ABS_HAT0Y

def hat_from_axes(x: int, y: int) -> int:
    if x == 0 and y == 0:
        return 8
    table = {
        (0, -1): 0, (1, -1): 1, (1,  0): 2, (1,  1): 3,
        (0,  1): 4, (-1, 1): 5, (-1, 0): 6, (-1,-1): 7,
    }
    return table.get((x, y), 8)

DPAD_BUTTONS = {
    e.BTN_DPAD_UP:    (0, -1),
    e.BTN_DPAD_DOWN:  (0,  1),
    e.BTN_DPAD_LEFT:  (-1, 0),
    e.BTN_DPAD_RIGHT: (1,  0),
}

# ---------------------------------------------------------------- normalization
TRIGGER_AXES = set()

def normalize_axis(evdev_code: int, value: int, dev_info: dict) -> int:
    info = dev_info.get(evdev_code)
    if info is None:
        return 0
    lo, hi = info.min, info.max
    mid = (lo + hi) // 2
    span = max(1, (hi - lo) // 2)
    v = (value - mid) * 127 // span
    return max(-127, min(127, v))

def button_bit_index(evdev_code: int) -> int:
    return BUTTON_MAP.get(evdev_code, 0)