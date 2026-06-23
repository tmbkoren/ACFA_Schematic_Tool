"""Decal data extraction and random decal generation.

Note on float endianness: the boundary values in `DECAL_PART_DATA` are stored as
big-endian (">f"). `generate_random_decal_layer_alt` (used by the section/full
generators) reads and writes consistently as ">f". The older
`generate_random_decal_layer` is kept for reference and mixes ">f"/"<f"; the
endianness is intentional and must not be "normalized".
"""

import math
import random
import struct

from .constants import DECAL_PART_DATA
from .emblems import generate_random_emblem


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

    # --- Extract Data Block ---
    decal_data = schematic_block[DECAL_DATA_LOCAL_OFFSET:
                                 DECAL_DATA_LOCAL_OFFSET + DECAL_DATA_SIZE]

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
        raise ValueError(
            f"Invalid part_type. Must be one of {list(DECAL_PART_DATA.keys())}")

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
        layer_data[136 + i*4: 136 +
                   (i+1)*4] = struct.pack('<f', rand_rot_float)

    # 5. Scale (4 bytes) - Must be determined before position
    if current_scale_bytes is None:
        scale_largest_float = struct.unpack(
            '>f', part_data["scale_largest_bytes"])[0]
        scale_smallest_float = struct.unpack(
            '>f', part_data["scale_smallest_bytes"])[0]
        rand_scale_float = random.uniform(
            scale_largest_float, scale_smallest_float)
        final_scale_bytes = struct.pack('<f', rand_scale_float)
    else:
        final_scale_bytes = current_scale_bytes

    layer_data[160:164] = final_scale_bytes

    # 6. Position (12 bytes) - Dependent on scale
    # Unpack floats from bytes for calculation
    default_scale = struct.unpack('<f', part_data["default_scale_bytes"])[0]
    current_scale = struct.unpack('<f', final_scale_bytes)[0]

    # Calculate boundary constants for X and Y
    min_x_at_default = struct.unpack(
        '>f', part_data["min_x_at_default_bytes"])[0]
    max_x_at_default = struct.unpack(
        '>f', part_data["max_x_at_default_bytes"])[0]
    min_y_at_default = struct.unpack(
        '>f', part_data["min_y_at_default_bytes"])[0]
    max_y_at_default = struct.unpack(
        '>f', part_data["max_y_at_default_bytes"])[0]

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


def biased_scale(min_val=1.7, max_val=50, exponent=2.0):
    """
    Generate a float between min_val and max_val, biased toward min_val.
    exponent > 1 increases bias toward smaller numbers.
    exponent = 1 gives uniform distribution.
    """
    u = random.random()  # uniform 0..1
    biased = min_val + (max_val - min_val) * (u ** exponent)
    return biased


def generate_random_decal_layer_alt(part_type: str, current_scale_bytes: bytes | None = None) -> bytes:
    """
    Generates a single, random, and valid 164-byte decal layer.

    Coordinates (x, y) are restricted to default-scale min/max to avoid invalid values.
    Scale can still vary independently.

    Args:
        part_type: "head", "core", "arm_right", "arm_left", "legs".
        current_scale_bytes: Optional 4-byte float for scale. If None, a random scale is generated.

    Returns:
        164-byte bytes object representing one decal layer.
    """
    if part_type not in DECAL_PART_DATA:
        raise ValueError(
            f"Invalid part_type. Must be one of {list(DECAL_PART_DATA.keys())}")

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
        layer_data[136 + i*4: 140 + i*4] = struct.pack('>f', rand_rot_float)

    # 5. Scale (4 bytes)
    if current_scale_bytes is None:
        scale_largest = struct.unpack(
            '>f', part_data["scale_largest_bytes"])[0]
        scale_smallest = struct.unpack(
            '>f', part_data["scale_smallest_bytes"])[0]
        rand_scale_float = biased_scale(
            scale_largest, scale_smallest, exponent=5.0)
        final_scale_bytes = struct.pack('>f', rand_scale_float)
    else:
        final_scale_bytes = current_scale_bytes
    layer_data[160:164] = final_scale_bytes

    # 6. Position (12 bytes) — clamp to default-scale ranges
    min_x = struct.unpack('>f', part_data["min_x_at_default_bytes"])[0]
    max_x = struct.unpack('>f', part_data["max_x_at_default_bytes"])[0]
    min_y = struct.unpack('>f', part_data["min_y_at_default_bytes"])[0]
    max_y = struct.unpack('>f', part_data["max_y_at_default_bytes"])[0]

    rand_pos_x = random.uniform(min_x, max_x)
    rand_pos_y = random.uniform(min_y, max_y)

    layer_data[148:152] = struct.pack('>f', rand_pos_x)
    layer_data[152:156] = struct.pack('>f', rand_pos_y)

    # 7. Z position (4 bytes)
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
        raise ValueError(
            f"Invalid part_type. Must be one of {list(DECAL_PART_DATA.keys())}")

    decal_section_data = bytearray()
    for i in range(8):  # 8 layers per section
        decal_section_data.extend(
            generate_random_decal_layer_alt(part_type, current_scale_bytes))

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
