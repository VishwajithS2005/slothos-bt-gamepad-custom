"""HID Report Descriptor spoofing an Xbox Wireless Controller."""

REPORT_ID = 0x01
REPORT_BYTES = 11  # 1 (id) + 3 (btns) + 1 (hat+pad) + 6 (axes)

HID_DESCRIPTOR = bytes([
    0x05, 0x01,        # Usage Page (Generic Desktop Ctrls)
    0x09, 0x05,        # Usage (Game Pad)
    0xA1, 0x01,        # Collection (Application)
    0x85, REPORT_ID,   #   Report ID (1)
    
    # ---- 15 buttons (3 bytes with padding) ----
    0x05, 0x09,        #   Usage Page (Button)
    0x19, 0x01,        #   Usage Minimum (0x01)
    0x29, 0x0F,        #   Usage Maximum (0x0F)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x01,        #   Logical Maximum (1)
    0x75, 0x01,        #   Report Size (1)
    0x95, 0x0F,        #   Report Count (15)
    0x81, 0x02,        #   Input (Data,Var,Abs)
    
    # Padding for buttons (15 bits + 9 bits pad = 24 bits / 3 bytes)
    0x75, 0x09,        #   Report Size (9)
    0x95, 0x01,        #   Report Count (1)
    0x81, 0x03,        #   Input (Constant,Var,Abs)
    
    # ---- D-pad hat ----
    0x05, 0x01,        #   Usage Page (Generic Desktop Ctrls)
    0x09, 0x39,        #   Usage (Hat switch)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x07,        #   Logical Maximum (7)
    0x35, 0x00,        #   Physical Minimum (0)
    0x46, 0x3B, 0x01,  #   Physical Maximum (315)
    0x65, 0x14,        #   Unit (Rotation, Degrees)
    0x55, 0x00,        #   Unit Exponent (0)
    0x75, 0x04,        #   Report Size (4)
    0x95, 0x01,        #   Report Count (1)
    0x81, 0x42,        #   Input (Data,Var,Abs,Null State)
    
    # Padding for hat (4 bits + 4 bits pad = 8 bits / 1 byte)
    0x75, 0x04,        #   Report Size (4)
    0x95, 0x01,        #   Report Count (1)
    0x81, 0x03,        #   Input (Constant,Var,Abs)
    
    # ---- X / Y (Left stick) ----
    0x05, 0x01,        #   Usage Page (Generic Desktop)
    0x09, 0x30,        #   Usage (X)
    0x09, 0x31,        #   Usage (Y)
    0x15, 0x81,        #   Logical Minimum (-127)
    0x25, 0x7F,        #   Logical Maximum (127)
    0x75, 0x08,        #   Report Size (8)
    0x95, 0x02,        #   Report Count (2)
    0x81, 0x02,        #   Input (Data,Var,Abs)
    
    # ---- Z / Rz (Right stick) ----
    0x09, 0x32,        #   Usage (Z)
    0x09, 0x35,        #   Usage (Rz)
    0x15, 0x81,        #   Logical Minimum (-127)
    0x25, 0x7F,        #   Logical Maximum (127)
    0x75, 0x08,        #   Report Size (8)
    0x95, 0x02,        #   Report Count (2)
    0x81, 0x02,        #   Input (Data,Var,Abs)
    
    # ---- Brake / Gas (L2 / R2 Triggers) ----
    0x05, 0x02,        #   Usage Page (Simulation Ctrls)
    0x09, 0xC5,        #   Usage (Brake - L2)
    0x09, 0xC4,        #   Usage (Accelerator/Gas - R2)
    0x15, 0x00,        #   Logical Minimum (0)
    0x25, 0x7F,        #   Logical Maximum (127)
    0x75, 0x08,        #   Report Size (8)
    0x95, 0x02,        #   Report Count (2)
    0x81, 0x02,        #   Input (Data,Var,Abs)
    
    0xC0,              # End Collection
])

DESC_BYTES = HID_DESCRIPTOR