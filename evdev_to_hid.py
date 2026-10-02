"""evdev event code -> HID report field mapping for the ANBERNIC RG35XX H."""

import evdev.ecodes as e

# Spoofing standard Xbox Wireless Controller layout based strictly on RG35XX H hardware codes
# Ignored standard e.BTN_* definitions as the Anbernic firmware reuses codes arbitrarily.
BUTTON_MAP = {
    304: 1,   # A -> Xbox A
    305: 2,   # B -> Xbox B
    307: 3,   # X -> Xbox X
    306: 4,   # Y -> Xbox Y
    308: 5,   # L1 -> Xbox LB
    309: 6,   # R1 -> Xbox RB
    310: 7,   # Select -> Xbox View
    311: 8,   # Start -> Xbox Menu
    313: 9,   # L3 -> Xbox LSB
    316: 10,  # R3 -> Xbox RSB
    312: 11,  # Function -> Xbox Logo
}

# Translate digital shoulder buttons into Analog Trigger Axes
# (offset 4 = Brake/LT, offset 5 = Gas/RT in the 6-byte axis block)
TRIGGER_BUTTON_AXES = {
    314: (4, 127),  # L2 button -> Xbox LT (Brake)
    315: (5, 127),  # R2 button -> Xbox RT (Gas)
}

# Mapping exact Anbernic numerical axis codes to Xbox HID offsets
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