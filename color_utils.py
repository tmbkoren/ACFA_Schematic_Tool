import random
from typing import Tuple


def extract_color_data(schematic_block: bytes) -> Tuple[bytearray, bytearray, bytearray]:
    """
    Extracts color, pattern, and eye color data from a schematic block.

    The function calculates the local offsets for each data type based on their
    known absolute positions in the save file and returns them as mutable
    bytearrays.

    Args:
        schematic_block: A bytes object representing a single schematic block.

    Returns:
        A tuple containing three bytearrays:
        1. The main color data block (0x330 bytes).
        2. The pattern data block (0x24 bytes).
        3. The eye color data (0x4 bytes).
    """
    # Absolute address of the first schematic block in DESDOC.DAT
    SCHEMATIC_START_ABS = 0x148

    # --- Calculate Local Offsets ---
    # Colors: 0x290 (absolute) - 0x148 (schematic start) = 0x148 (local)
    COLORS_LOCAL_OFFSET = 0x148
    COLORS_SIZE = 0x330

    # Patterns: 0x5C0 (absolute) - 0x148 (schematic start) = 0x478 (local)
    PATTERNS_LOCAL_OFFSET = 0x478
    PATTERNS_SIZE = 0x24

    # Eye Color: 0x5E4 (absolute) - 0x148 (schematic start) = 0x49C (local)
    EYE_COLOR_LOCAL_OFFSET = 0x49C
    EYE_COLOR_SIZE = 0x4

    # --- Extract Data Blocks ---
    colors_data = schematic_block[COLORS_LOCAL_OFFSET:COLORS_LOCAL_OFFSET + COLORS_SIZE]
    patterns_data = schematic_block[PATTERNS_LOCAL_OFFSET:PATTERNS_LOCAL_OFFSET + PATTERNS_SIZE]
    eye_color_data = schematic_block[EYE_COLOR_LOCAL_OFFSET:EYE_COLOR_LOCAL_OFFSET + EYE_COLOR_SIZE]

    # Return as mutable bytearrays
    return bytearray(colors_data), bytearray(patterns_data), bytearray(eye_color_data)


def replace_color_data(
    schematic_block: bytes,
    new_colors: bytes = None,
    new_patterns: bytes = None,
    new_eye_color: bytes = None
) -> bytes:
    """
    Replaces specified color, pattern, or eye color data in a schematic block.

    If a replacement is not provided for a specific data block (i.e., the
    argument is None), the original data from the schematic_block is kept.

    Args:
        schematic_block: The original schematic block bytes.
        new_colors: Optional new color data (must be 0x330 bytes if provided).
        new_patterns: Optional new pattern data (must be 0x24 bytes if provided).
        new_eye_color: Optional new eye color data (must be 0x4 bytes if provided).

    Returns:
        A new schematic block bytes object with the specified data replaced.
    """
    # Define constants for offsets and sizes
    COLORS_LOCAL_OFFSET = 0x148
    COLORS_SIZE = 0x330
    PATTERNS_LOCAL_OFFSET = 0x478
    PATTERNS_SIZE = 0x24
    EYE_COLOR_LOCAL_OFFSET = 0x49C
    EYE_COLOR_SIZE = 0x4

    mutable_block = bytearray(schematic_block)

    # --- Conditionally Replace Data ---
    if new_colors is not None:
        if len(new_colors) != COLORS_SIZE:
            raise ValueError(
                f"Invalid colors data size. Expected {COLORS_SIZE}, got {len(new_colors)}.")
        mutable_block[COLORS_LOCAL_OFFSET:COLORS_LOCAL_OFFSET +
                      COLORS_SIZE] = new_colors

    if new_patterns is not None:
        if len(new_patterns) != PATTERNS_SIZE:
            raise ValueError(
                f"Invalid patterns data size. Expected {PATTERNS_SIZE}, got {len(new_patterns)}.")
        mutable_block[PATTERNS_LOCAL_OFFSET:PATTERNS_LOCAL_OFFSET +
                      PATTERNS_SIZE] = new_patterns

    if new_eye_color is not None:
        if len(new_eye_color) != EYE_COLOR_SIZE:
            raise ValueError(
                f"Invalid eye color data size. Expected {EYE_COLOR_SIZE}, got {len(new_eye_color)}.")
        mutable_block[EYE_COLOR_LOCAL_OFFSET:EYE_COLOR_LOCAL_OFFSET +
                      EYE_COLOR_SIZE] = new_eye_color

    return bytes(mutable_block)


def randomize_colors(colors_data: bytes) -> bytes:
    """
    Randomizes the RGB channels for all colors in a color data block.

    The alpha channel of each color is preserved as it is unused in-game.

    Args:
        colors_data: The color data block (e.g., 0x330 bytes).

    Returns:
        A new color data block with randomized RGB values.
    """
    if len(colors_data) % 4 != 0:
        raise ValueError(
            "Invalid colors data length. Length must be divisible by 4.")

    mutable_colors = bytearray(colors_data)

    # Iterate through each color (4 bytes at a time)
    for i in range(0, len(mutable_colors), 4):
        # Randomize R, G, B channels
        mutable_colors[i] = random.randint(0, 255)   # R
        mutable_colors[i+1] = random.randint(0, 255)  # G
        mutable_colors[i+2] = random.randint(0, 255)  # B
        # The 4th byte (alpha) at i+3 is intentionally left unchanged.

    return bytes(mutable_colors)
