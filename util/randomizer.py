"""Part swapping and randomization.

Block-level functions (``set_part_in_block``, ``random_part_id``,
``randomize_parts_in_block``) are the core and operate on in-memory schematic
blocks. The original file-based helpers (``swap_part_in_ac4a_file``,
``randomize_schematic_parts``) are kept as thin wrappers around them.
"""

import os
import random

from . import part_data
from .io_utils import save_file
from .schematic import display_schematic_info, load_schematic_block_from_ac4a

LOCAL_PARTS_OFFSET = 0xD8
PART_ENTRY_SIZE = 2
NAME_OFFSET = 1
NAME_SIZE = 96  # 48 UTF-16-LE code units

# The 15 physical part slots, in block order:
# (lookup key in part_mapping, human display label).
# Arm Unit / Back Unit each map to two physical slots (right/left).
PART_SLOTS = [
    ('Head', 'Head'),
    ('Core', 'Core'),
    ('Arms', 'Arms'),
    ('Legs', 'Legs'),
    ('FCS', 'FCS'),
    ('Generator', 'Generator'),
    ('Main Booster', 'Main Booster'),
    ('Back Booster', 'Back Booster'),
    ('Side Booster', 'Side Booster'),
    ('Overed Booster', 'Overed Booster'),
    ('Arm Unit', 'Right Arm Unit'),
    ('Arm Unit', 'Left Arm Unit'),
    ('Back Unit', 'Right Back Unit'),
    ('Back Unit', 'Left Back Unit'),
    ('Shoulder Unit', 'Shoulder Unit'),
]


def _valid_part_ids(part_mapping, lookup_key, include_debug=False):
    """All part-ID strings for a category. Debug parts (IDs starting with '9')
    are excluded unless ``include_debug``."""
    ids = list(part_mapping.get(lookup_key, {}).keys())
    if not include_debug:
        ids = [pid for pid in ids if not pid.startswith('9')]
    return ids


def set_part_in_block(block, slot_index, new_part_id):
    """Return a new block with ``slot_index`` (0..14) set to ``new_part_id``
    (int or numeric string), written big-endian into the parts table."""
    if not (0 <= slot_index < len(PART_SLOTS)):
        raise ValueError(f"slot_index out of range: {slot_index}")
    part_id_num = int(new_part_id)
    offset = LOCAL_PARTS_OFFSET + slot_index * PART_ENTRY_SIZE
    mutable_block = bytearray(block)
    mutable_block[offset:offset + PART_ENTRY_SIZE] = part_id_num.to_bytes(2, 'big')
    return bytes(mutable_block)


def random_part_id(part_mapping, lookup_key, include_debug=False):
    """Pick a random valid part-ID string for a category, or None if none."""
    ids = _valid_part_ids(part_mapping, lookup_key, include_debug)
    return random.choice(ids) if ids else None


def randomize_parts_in_block(block, part_mapping=None, slots=None, include_debug=False):
    """Return a new block with the given slot indices randomized.

    ``slots`` is an iterable of slot indices (0..14); None means all 15.
    ``part_mapping`` defaults to the module-level mapping.
    """
    if part_mapping is None:
        part_mapping = part_data.get_part_mapping()
    if slots is None:
        slots = range(len(PART_SLOTS))

    mutable_block = bytearray(block)
    for i in slots:
        lookup_key, _ = PART_SLOTS[i]
        pid = random_part_id(part_mapping, lookup_key, include_debug)
        if pid is None:
            continue
        offset = LOCAL_PARTS_OFFSET + i * PART_ENTRY_SIZE
        mutable_block[offset:offset + PART_ENTRY_SIZE] = int(pid).to_bytes(2, 'big')
    return bytes(mutable_block)


def set_name_in_block(block, new_name):
    """Return a new block with the schematic name field replaced (truncated to
    fit the 96-byte UTF-16-LE field)."""
    max_chars = (NAME_SIZE // 2) - 1
    if len(new_name) > max_chars:
        new_name = new_name[:max_chars]
    name_buffer = bytearray(NAME_SIZE)
    encoded = new_name.encode('utf-16-le')
    name_buffer[:len(encoded)] = encoded
    mutable_block = bytearray(block)
    mutable_block[NAME_OFFSET:NAME_OFFSET + NAME_SIZE] = name_buffer
    return bytes(mutable_block)


# --- File-based wrappers (kept for the notebooks) -----------------------

def swap_part_in_ac4a_file(file_path, part_category, new_part_id):
    """Read an .ac4a, swap a part (by display label, e.g. 'Right Arm Unit'),
    and save it back to the same file."""
    display_labels = [label for _, label in PART_SLOTS]
    try:
        slot_index = display_labels.index(part_category)
    except ValueError:
        raise ValueError(
            f"Invalid part category: {part_category}. Must be one of {display_labels}")

    try:
        block = load_schematic_block_from_ac4a(file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    block = set_part_in_block(block, slot_index, new_part_id)
    save_file(file_path, block)
    print(f"Swapped '{part_category}' to part ID {new_part_id} in {file_path}.")


def randomize_schematic_parts(file_path, part_mapping, new_name=None):
    """Read an .ac4a, randomize all parts (excluding debug), optionally rename,
    save to a new file, and return the output path."""
    try:
        block = load_schematic_block_from_ac4a(file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    block = randomize_parts_in_block(block, part_mapping)

    if new_name:
        block = set_name_in_block(block, new_name)
        output_dir = os.path.dirname(file_path)
        output_path = os.path.join(output_dir, f"{new_name}.ac4a")
    else:
        output_path = file_path

    save_file(output_path, block)
    print(f"Saved randomized schematic to {output_path}.")
    return output_path
