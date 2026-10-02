"""evdev event code -> HID report field mapping for the ANBERNIC RG35XX H."""

import evdev.ecodes as e

# ---------------------------------------------------------------- buttons
# Corrected to align with standard Android/Linux HID Gamepad mapping
BUTTON_MAP = {
    # Standard gamepad face
    e.BTN_SOUTH:   1,   # 304 (A) -> Android BTN_A
    e.BTN_EAST:    2,   # 305 (B) -> Android BTN_B
    e.BTN_C:       4,   # 306 (X) -> Android BTN_X
    e.BTN_NORTH:   5,   # 307 (Y) -> Android BTN_Y

    # Shoulders
    e.BTN_TL:      7,   # 310 (L1) -> Android BTN_L1
    e.BTN_TR:      8,   # 311 (R1) -> Android BTN_R1

    # Triggers
    e.BTN_TL2:     9,   # 312 (L2) -> Android BTN_L2
    e.BTN_TR2:     10,  # 313 (R2) -> Android BTN_R2

    # Select / Start / Mode
    e.BTN_SELECT:  11,  # 314 (Select) -> Android BTN_SELECT
    e.BTN_START:   12,  # 315 (Start) -> Android BTN_START
    e.BTN_MODE:    13,  # 316 (Mode) -> Android BTN_MODE

    # Stick Clicks
    e.BTN_WEST:    14,  # 308 (L3) -> Android BTN_THUMBL
    e.BTN_Z:       15,  # 309 (R3) -> Android BTN_THUMBR

    # Extra system keys (Mapped higher to prevent overlapping gamepad inputs)
    e.KEY_GOTO:        16,
    e.KEY_ESC:         17,
    e.KEY_VOLUMEDOWN:  18,
    e.KEY_VOLUMEUP:    19,
}

# ---------------------------------------------------------------- axes
AXIS_MAP = {
    e.ABS_Z:    0,   # LEFT  stick X -> HID X
    e.ABS_RZ:   1,   # LEFT  stick Y -> HID Y
    
    # RIGHT stick strictly mapped to HID Z and Rz for standard Android support
    e.ABS_RX:   2,   # RIGHT stick X -> HID Z
    e.ABS_RY:   3,   # RIGHT stick Y -> HID Rz
}

# Aliases for kernels that expose sticks under non-standard codes
AXIS_ALIASES = {}

# ---------------------------------------------------------------- D-pad
DPAD_AXIS_X = e.ABS_HAT0X
DPAD_AXIS_Y = e.ABS_HAT0Y

def hat_from_axes(x: int, y: int) -> int:
    if x == 0 and y == 0:
        return 8  # null / released
    table = {
        (0, -1): 0,
        (1, -1): 1,
        (1,  0): 2,
        (1,  1): 3,
        (0,  1): 4,
        (-1, 1): 5,
        (-1, 0): 6,
        (-1,-1): 7,
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
    code = AXIS_ALIASES.get(evdev_code, evdev_code)
    if code in TRIGGER_AXES:
        info = dev_info.get(evdev_code)
        if info is None:
            return 0 if value == 0 else 127
        lo, hi = info.min, info.max
        span = max(1, hi - lo)
        v = (value - lo) * 127 // span
        return max(0, min(127, v))
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