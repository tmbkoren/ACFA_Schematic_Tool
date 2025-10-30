import random
import struct
import math
from emblem_utils import generate_random_emblem

# --- Data Structure for Part-Specific Decal Boundaries ---
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


def extract_decal_data(schematic_block: bytes) -> bytearray:
    """
    Extracts decal data from a schematic block.

    The function calculates the local offset for the decal data based on its
    known absolute position in the save file and returns it as a mutable
    bytearray.

    Args:
        schematic_block: A bytes object representing a single schematic block.

    Returns:
        A bytearray containing the decal data (0x19A0 bytes).
    """
    # Absolute address of the first schematic block in DESDOC.DAT
    SCHEMATIC_START_ABS = 0x148

    # Decals: 0x5E8 (absolute) - 0x148 (schematic start) = 0x4A0 (local)
    DECAL_DATA_LOCAL_OFFSET = 0x4A0
    DECAL_DATA_SIZE = 0x19A0

    # 5 sections; head, core, arm_right, arm_left, legs
    # each of size 520h 
    # each section is of 8 layers, each layer is A4h bytes
    # each layer starts with image, 84h bytes, identical to the emblem data structure
    # followed by:
    # width (1 byte) 3-255
    # height (1 byte) 3-255
    # unknown (2 bytes) usually 0000
    # rotation section, Ch bytes
    #   x rotation 4h bytes float (-3.14 to 3.14 approximately, assume -pi to pi)
    #   y rotation 4h bytes float (-3.12 to 3.12 approximately, assume -pi to pi)
    #   z rotation 4h bytes float (-3.14 to 3.14 approximately, assume -pi to pi)
    # position section, Ch bytes
    #   x position 4h bytes float 
    #       with default scaling factors applied:
    #       head ranges: neutral position is B4 CC 9C B8 (-0.00000038 approximately), min value: BF 59 99 A0 (-0.85 approximately), max value: 3F 59 99 94 (0.8499997 approximately)
    #       core ranges: neutral position is BB F5 F3 20 (-0.0075 approximately), min value: C0 15 EB 6E (-2.34 approximately), max value: 40 14 F5 7A (2.3275 approximately)
    #       right arms ranges: neutral position is 3F 7B 4D CA (0.982 approximately), min value: BF FD C2 F5 (-1.982 approximately), max value: 40 7C 88 60 (3.946 approximately)
    #       left arms ranges: neutral position is BF 7B 4D AE (-0.982 approximately), min value: C0 07 88 58 (-3.946 approximately), max value: 3F FD C3 03 (1.983 approximately)
    #       legs ranges: neutral position is 35 AF 1A 5F (0.0000013 approximately), min value: C0 5A 9B E8 (-3.146 approximately), max value: 40 5A 9B F2 (3.146 approximately)
    #   y position 4h bytes float
    #       with default scaling factors applied:
    #       head ranges: neutral position is BE DC 73 00 (-0.431 approximately), min value: BF A3 E9 8D (-1.281 approximately), max value: 3E D6 C0 34 (0.419 approximately)
    #       core ranges: neutral position is BF B4 6A E0 (-1.409 approximately), min value: C0 6F A5 E4 (-3.745 approximately), max value: 3F 6C EC 10 (0.925 approximately)
    #       right arms ranges: neutral position is 3F 1B 1C A9 (0.606 approximately), min value: C0 16 ED C3 (-2.358 approximately), max value: 40 64 7C 17 (3.570 approximately)
    #       left arms ranges: neutral position is 3F 1B 1C B3 (0.6059 approximately), min value: C0 16 ED C0 (-2.358 approximately), max value: 40 64 7C 1A (3.570 approximately)
    #       legs ranges: neutral position is 40 73 52 F8 (3.802 approximately), min value: 3E C5 B8 58 (0.386 approximately), max value: 40 E6 F7 72 (7.218 approximately)
    #   z position 4h bytes float (head: C0 EC FB 3F; core: C0 40 98 4F, right arm: BF D2 2B B2, left arm: BF D2 2B BA, legs: 3F 06 98 53)
    # scale section, 4h bytes float
    # scale_value_for_largest_visual_size: A smaller numerical float value (e.g., 1.7) makes the part appear largest.
    # scale_value_for_smallest_visual_size: A larger numerical float value (e.g., 50) makes the part appear smallest.
    # head default value: 3F D9 99 9A (1.7 approximately)
    #   scale_value_for_largest_visual_size: 3F D9 99 9A (1.7 approximately)
    #   scale_value_for_smallest_visual_size: 42 48 00 00 (50 decimal)
    # core default value: 40 95 70 74 (4.669977 approximately)
    #   scale_value_for_largest_visual_size: 3F D9 99 9A (1.7 approximately)
    #   scale_value_for_smallest_visual_size: 42 48 00 00 (50 decimal)
    # both arms default value: 40 BD B4 ED (5.928336 approximately)
    #   scale_value_for_largest_visual_size: 3F D9 99 9A (1.7 approximately)
    #   scale_value_for_smallest_visual_size: 42 48 00 00 (50 decimal)
    # legs default value: 40 DA 9B ED (6.831534 approximately)
    #   scale_value_for_largest_visual_size: 3F D9 99 9A (1.7 approximately)
    #   scale_value_for_smallest_visual_size: 42 48 00 00 (50 decimal)
    # --- Extract Data Block ---
    decal_data = schematic_block[DECAL_DATA_LOCAL_OFFSET:DECAL_DATA_LOCAL_OFFSET + DECAL_DATA_SIZE]

    # Return as a mutable bytearray
    return bytearray(decal_data)


def replace_decal_data(
    schematic_block: bytes,
    new_decal_data: bytes
) -> bytes:
    """
    Replaces the decal data in a schematic block.

    Args:
        schematic_block: The original schematic block bytes.
        new_decal_data: New decal data (must be 0x19A0 bytes).

    Returns:
        A new schematic block bytes object with the decal data replaced.
    """
    # Define constants for offset and size
    DECAL_DATA_LOCAL_OFFSET = 0x4A0
    DECAL_DATA_SIZE = 0x19A0

    if len(new_decal_data) != DECAL_DATA_SIZE:
        raise ValueError(
            f"Invalid decal data size. Expected {DECAL_DATA_SIZE}, got {len(new_decal_data)}.")

    mutable_block = bytearray(schematic_block)
    mutable_block[DECAL_DATA_LOCAL_OFFSET:DECAL_DATA_LOCAL_OFFSET +
                  DECAL_DATA_SIZE] = new_decal_data

    return bytes(mutable_block)

def generate_random_decal_layer(part_type: str, current_scale_bytes: bytes | None = None) -> bytes:
    """
    Generates a single, random, and valid 164-byte decal layer.

    Args:
        part_type: The type of part, e.g., "head", "core", "arm_right", "arm_left", "legs".
        current_scale_bytes: Optional. The 4-byte float representation of the current scale.
                             If None, a random scale for the part will be generated.

    Returns:
        A 164-byte `bytes` object representing a complete decal layer.
    """
    if part_type not in DECAL_PART_DATA:
        raise ValueError(f"Invalid part_type. Must be one of {list(DECAL_PART_DATA.keys())}")

    part_data = DECAL_PART_DATA[part_type]
    layer_data = bytearray(164)

    # 1. Emblem (132 bytes)
    layer_data[0:132] = generate_random_emblem()

    # 2. Width and Height (1 byte each)
    layer_data[132] = random.randint(3, 255)
    layer_data[133] = random.randint(3, 255)

    # 3. Unknown (2 bytes)
    layer_data[134:136] = bytes([0, 0])

    # 4. Rotation (12 bytes)
    for i in range(3):
        rand_rot_float = random.uniform(-math.pi, math.pi)
        layer_data[136 + i*4 : 136 + (i+1)*4] = struct.pack('<f', rand_rot_float)

    # 5. Scale (4 bytes) - Must be determined before position
    if current_scale_bytes is None:
        scale_largest_float = struct.unpack('<f', part_data["scale_largest_bytes"])[0]
        scale_smallest_float = struct.unpack('<f', part_data["scale_smallest_bytes"])[0]
        rand_scale_float = random.uniform(scale_largest_float, scale_smallest_float)
        final_scale_bytes = struct.pack('<f', rand_scale_float)
    else:
        final_scale_bytes = current_scale_bytes
    
    layer_data[160:164] = final_scale_bytes

    # 6. Position (12 bytes) - Dependent on scale
    # Unpack floats from bytes for calculation
    default_scale = struct.unpack('<f', part_data["default_scale_bytes"])[0]
    current_scale = struct.unpack('<f', final_scale_bytes)[0]

    # Calculate boundary constants for X and Y
    min_x_at_default = struct.unpack('<f', part_data["min_x_at_default_bytes"])[0]
    max_x_at_default = struct.unpack('<f', part_data["max_x_at_default_bytes"])[0]
    min_y_at_default = struct.unpack('<f', part_data["min_y_at_default_bytes"])[0]
    max_y_at_default = struct.unpack('<f', part_data["max_y_at_default_bytes"])[0]

    const_min_x = min_x_at_default * default_scale
    const_max_x = max_x_at_default * default_scale
    const_min_y = min_y_at_default * default_scale
    const_max_y = max_y_at_default * default_scale

    # Calculate dynamic range for the current scale
    current_min_x = const_min_x / current_scale
    current_max_x = const_max_x / current_scale
    current_min_y = const_min_y / current_scale
    current_max_y = const_max_y / current_scale

    # Generate random floats within the dynamic range and pack them
    rand_pos_x = random.uniform(current_min_x, current_max_x)
    rand_pos_y = random.uniform(current_min_y, current_max_y)
    
    layer_data[148:152] = struct.pack('<f', rand_pos_x)
    layer_data[152:156] = struct.pack('<f', rand_pos_y)
    layer_data[156:160] = part_data["z_pos_bytes"]

    return bytes(layer_data)

def generate_random_decal_section(part_type: str, current_scale_bytes: bytes | None = None) -> bytes:
    """
    Generates a complete, random 1312-byte (0x520) decal section for a given part type.

    A decal section consists of 8 individual decal layers.

    Args:
        part_type: The type of part, e.g., "head", "core", "arm_right", "arm_left", "legs".
        current_scale_bytes: Optional. The 4-byte float representation of the current scale.
                             If None, a random scale for the part will be generated for each layer.

    Returns:
        A 1312-byte `bytes` object representing a complete decal section.
    """
    if part_type not in DECAL_PART_DATA:
        raise ValueError(f"Invalid part_type. Must be one of {list(DECAL_PART_DATA.keys())}")

    decal_section_data = bytearray()
    for _ in range(8):  # 8 layers per section
        decal_section_data.extend(generate_random_decal_layer(part_type, current_scale_bytes))

    return bytes(decal_section_data)

def generate_full_random_decal_data() -> bytes:
    """
    Generates a full random decal data block (0x19A0 bytes) for all parts.

    Returns:
        A bytes object representing the complete decal data for all parts.
    """
    full_decal_data = bytearray()

    for part in ["head", "core", "arm_right", "arm_left", "legs"]:
        section_data = generate_random_decal_section(part)
        full_decal_data.extend(section_data)

    return bytes(full_decal_data)
