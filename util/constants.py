"""Shared constants for the ACFA schematic toolkit."""

# A single schematic block in DESDOC.DAT / a .ac4a file.
BLOCK_SIZE = 24280
# Name / designer field width: 48 wchar_t = 96 bytes in UTF-16-LE.
NAME_SIZE = 96

# Constant 16-byte header that prefixes every ACFA thumbnail (DXT1 image follows).
ACFA_THUMBNAIL_HEADER = bytes([
    0x10, 0x00, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x40, 0x00
])

# Per-part decal boundary data. Float fields are stored as big-endian (">f")
# 4-byte hex; see decals.py for how they are interpreted.
DECAL_PART_DATA = {
    "head": {
        "default_scale_bytes": bytes.fromhex("3FD9999A"),
        "scale_largest_bytes": bytes.fromhex("3FD9999A"),
        "scale_smallest_bytes": bytes.fromhex("42480000"),
        "min_x_at_default_bytes": bytes.fromhex("BF5999A0"),
        "max_x_at_default_bytes": bytes.fromhex("3F599994"),
        "min_y_at_default_bytes": bytes.fromhex("BFA3E98D"),
        "max_y_at_default_bytes": bytes.fromhex("3ED6C034"),
        "z_pos_bytes": bytes.fromhex("C0ECFB3F"),
    },
    "core": {
        "default_scale_bytes": bytes.fromhex("40957074"),
        "scale_largest_bytes": bytes.fromhex("3FD9999A"),
        "scale_smallest_bytes": bytes.fromhex("42480000"),
        "min_x_at_default_bytes": bytes.fromhex("C015EB6E"),
        "max_x_at_default_bytes": bytes.fromhex("4014F57A"),
        "min_y_at_default_bytes": bytes.fromhex("C06FA5E4"),
        "max_y_at_default_bytes": bytes.fromhex("3F6CEC10"),
        "z_pos_bytes": bytes.fromhex("C040984F"),
    },
    "arm_right": {
        "default_scale_bytes": bytes.fromhex("40BDB4ED"),
        "scale_largest_bytes": bytes.fromhex("3FD9999A"),
        "scale_smallest_bytes": bytes.fromhex("42480000"),
        "min_x_at_default_bytes": bytes.fromhex("BFFDC2F5"),
        "max_x_at_default_bytes": bytes.fromhex("407C8860"),
        "min_y_at_default_bytes": bytes.fromhex("C016EDC3"),
        "max_y_at_default_bytes": bytes.fromhex("40647C17"),
        "z_pos_bytes": bytes.fromhex("BFD22BB2"),
    },
    "arm_left": {
        "default_scale_bytes": bytes.fromhex("40BDB4ED"),
        "scale_largest_bytes": bytes.fromhex("3FD9999A"),
        "scale_smallest_bytes": bytes.fromhex("42480000"),
        "min_x_at_default_bytes": bytes.fromhex("C0078858"),
        "max_x_at_default_bytes": bytes.fromhex("3FFDC303"),
        "min_y_at_default_bytes": bytes.fromhex("C016EDC0"),
        "max_y_at_default_bytes": bytes.fromhex("40647C1A"),
        "z_pos_bytes": bytes.fromhex("BFD22BBA"),
    },
    "legs": {
        "default_scale_bytes": bytes.fromhex("40DA9BED"),
        "scale_largest_bytes": bytes.fromhex("3FD9999A"),
        "scale_smallest_bytes": bytes.fromhex("42480000"),
        "min_x_at_default_bytes": bytes.fromhex("C05A9BE8"),
        "max_x_at_default_bytes": bytes.fromhex("405A9BF2"),
        "min_y_at_default_bytes": bytes.fromhex("3EC5B858"),
        "max_y_at_default_bytes": bytes.fromhex("40E6F772"),
        "z_pos_bytes": bytes.fromhex("3F069853"),
    },
}
