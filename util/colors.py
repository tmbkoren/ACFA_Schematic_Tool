"""Color, pattern, and eye-color regions of a schematic block."""

import random
from typing import Tuple

# --- Color region structure (verified in-game) ---
# The 0x330-byte color blob is 34 sections x 6 colors x 4 bytes (RGBA), NOT a
# flat array. Sections 0-11 are the 12 UI-visible parts (Head, Core, R Arm,
# L Arm, Legs, R/L Arm Unit, R/L Back Unit, Shoulder, R/L Hanger Unit); sections
# 12-33 are the 22 stabilizers (paintable in-game but hidden from the preview
# list). The 6 colors are Main, Sub, Support, Optional, Joint, Device. The 4th
# byte per color is an unknown per-color finish/material setting (NOT alpha).
TOTAL_COLOR_SECTIONS = 34
VISIBLE_COLOR_SECTIONS = 12  # stabilizers (12-33) are excluded from editing
COLORS_PER_SECTION = 6
BYTES_PER_COLOR = 4
SECTION_BYTES = COLORS_PER_SECTION * BYTES_PER_COLOR  # 24

# Names for the 12 visible sections (in file order) and the 6 colors per section.
COLOR_SECTION_NAMES = (
    "Head", "Core", "R Arm", "L Arm", "Legs",
    "R Arm Unit", "L Arm Unit", "R Back Unit", "L Back Unit",
    "Shoulder Unit", "R Hanger Unit", "L Hanger Unit",
)
COLOR_CHANNEL_NAMES = ("Main", "Sub", "Support", "Optional", "Joint", "Device")


def extract_visible_swatches(colors_data: bytes) -> list[list[Tuple[int, int, int]]]:
    """
    Parses the color blob into the 12 visible sections for display.

    Returns a list of 12 sections, each a list of 6 ``(r, g, b)`` tuples in
    ``COLOR_CHANNEL_NAMES`` order. The 22 stabilizer sections and the unused 4th
    byte of each color are ignored.

    Args:
        colors_data: The color data block (0x330 bytes).

    Returns:
        ``[[(r, g, b), ...6], ...12]``.
    """
    swatches = []
    for section in range(VISIBLE_COLOR_SECTIONS):
        base = section * SECTION_BYTES
        colors = []
        for channel in range(COLORS_PER_SECTION):
            off = base + channel * BYTES_PER_COLOR
            colors.append((colors_data[off], colors_data[off + 1], colors_data[off + 2]))
        swatches.append(colors)
    return swatches


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
    new_colors: bytes | None = None,
    new_patterns: bytes | None = None,
    new_eye_color: bytes | None = None
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
    Randomizes the RGB channels for the 12 UI-visible color sections.

    The 22 stabilizer sections (12-33) are intentionally left untouched, matching
    the rest of the tool's "don't randomize stabilizers" stance. The 4th byte of
    each color (an unknown per-color finish/material setting) is also preserved.

    Args:
        colors_data: The color data block (0x330 bytes).

    Returns:
        A new color data block with randomized RGB values on the visible sections.
    """
    if len(colors_data) % 4 != 0:
        raise ValueError(
            "Invalid colors data length. Length must be divisible by 4.")

    mutable_colors = bytearray(colors_data)

    # Only the first 12 (visible) sections; skip the 22 stabilizer sections.
    randomize_limit = min(
        len(mutable_colors), VISIBLE_COLOR_SECTIONS * SECTION_BYTES)

    # Iterate through each color (4 bytes at a time)
    for i in range(0, randomize_limit, BYTES_PER_COLOR):
        # Randomize R, G, B channels
        mutable_colors[i] = random.randint(0, 255)   # R
        mutable_colors[i+1] = random.randint(0, 255)  # G
        mutable_colors[i+2] = random.randint(0, 255)  # B
        # The 4th byte at i+3 is intentionally left unchanged.

    return bytes(mutable_colors)
