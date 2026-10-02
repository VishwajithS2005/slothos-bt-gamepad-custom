"""evdev event code -> HID report field mapping for the ANBERNIC RG35XX H."""

import evdev.ecodes as e

# Spoofing standard Xbox Wireless Controller layout
BUTTON_MAP = {
    e.BTN_SOUTH:   1,   # 304 (A) -> Xbox A
    e.BTN_EAST:    2,   # 305 (B) -> Xbox B
    e.BTN_NORTH:   3,   # 307 (X) -> Xbox X
    e.BTN_WEST:    4,   # 308 (Y) -> Xbox Y
    e.BTN_TL:      5,   # 310 (L1) -> Xbox LB
    e.BTN_TR:      6,   # 311 (R1) -> Xbox RB
    e.BTN_SELECT:  7,   # 314 (Select) -> Xbox View
    e.BTN_START:   8,   # 315 (Start) -> Xbox Menu
    e.BTN_WEST:    9,   # L3 (Stick click fallback) -> Xbox LSB
    e.BTN_Z:       10,  # R3 (Stick click fallback) -> Xbox RSB
    e.BTN_MODE:    11,  # 316 (Mode) -> Xbox Logo
}

# Translate digital shoulder buttons into Analog Trigger Axes
# (offset 4 = Brake/L2, offset 5 = Gas/R2 in the 6-byte axis block)
TRIGGER_BUTTON_AXES = {
    e.BTN_TL2: (4, 127),  # 312 (L2) 
    e.BTN_TR2: (5, 127),  # 313 (R2) 
}

AXIS_MAP = {
    e.ABS_Z:    0,   # LEFT stick X -> HID X (offset 0)
    e.ABS_RZ:   1,   # LEFT stick Y -> HID Y (offset 1)
    e.ABS_RX:   2,   # RIGHT stick X -> HID Z (offset 2)
    e.ABS_RY:   3,   # RIGHT stick Y -> HID Rz (offset 3)
}

AXIS_ALIASES = {}

# ---------------------------------------------------------------- D-pad
DPAD_AXIS_X = e.ABS_HAT0X
DPAD_AXIS_Y = e.ABS_HAT0Y

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