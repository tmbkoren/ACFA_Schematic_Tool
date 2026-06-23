"""Reading and writing whole schematic blocks: parts, tuning, names, and the
DESDOC.DAT <-> .ac4a exchange."""

import os
import re
import struct

from . import part_data
from .constants import BLOCK_SIZE, NAME_SIZE
from .io_utils import backup_desdoc, load_file, save_file


def linear_utf16_clean_name_reader(data, start_offset, max_bytes=96):
    raw_field = data[start_offset:start_offset + max_bytes]
    try:
        decoded = raw_field.decode('utf-16-le', errors='ignore').strip('\x00')
        # Permissive: allow spaces, underscores, hyphens and dots in names
        # (ported from the GUI's reader so names like "AC-01.B" survive).
        match = re.match(r'^[A-Za-z0-9 _\-.]+', decoded)
        if match:
            return match.group(0).strip()
        return "<Invalid UTF-16 Encoding>"
    except UnicodeDecodeError:
        return "<Invalid UTF-16 Encoding>"


def read_timestamp(data, offset):
    timestamp_bytes = data[offset:offset + 8]
    return struct.unpack(">Q", timestamp_bytes)[0]


def extract_active_schematic_blocks(file_path):
    """
    Extracts all schematic blocks from the given file.
    Returns a list of blocks.
    """
    data = load_file(file_path)
    schematic_count = data[5]
    blocks = []
    first_marker_offset = 0x148

    for slot_index in range(schematic_count):
        block_start = first_marker_offset + (slot_index * BLOCK_SIZE)
        block = data[block_start:block_start + BLOCK_SIZE]
        blocks.append(block)
    return blocks


def display_schematic_info(block, part_mapping=None):
    """
    Displays the schematic information from a block.
    Returns a dictionary with the schematic information.

    ``part_mapping`` is optional; when omitted, the module-level mapping is used
    (resolved lazily so a value-import captured at start-up can't go stale).
    """
    if part_mapping is None:
        part_mapping = part_data.get_part_mapping()

    schematic_name = linear_utf16_clean_name_reader(block, 1, NAME_SIZE)
    designer_name = linear_utf16_clean_name_reader(
        block, 1 + NAME_SIZE, NAME_SIZE)
    timestamp = read_timestamp(block, 192)

    protect_category_byte = block[200]
    protect = (protect_category_byte & 0b10000000) >> 7
    category = (protect_category_byte & 0b01111111) + 1

    parts = extract_parts(block, part_mapping)
    tuning = extract_tuning(block)

    schematic_info = {
        "name": schematic_name,
        "designer": designer_name,
        "category": category,
        "timestamp": timestamp,
        "parts": parts,
        "tuning": tuning
    }

    return schematic_info


def extract_parts(block, part_name_lookup):
    LOCAL_PARTS_OFFSET = 0xD8  # 0x220 - 0x148
    PART_ENTRY_SIZE = 2

    # Define lookup keys and display labels separately
    lookup_keys = [
        'Head', 'Core', 'Arms', 'Legs', 'FCS', 'Generator', 'Main Booster',
        'Back Booster', 'Side Booster', 'Overed Booster',
        'Arm Unit', 'Arm Unit', 'Back Unit', 'Back Unit', 'Shoulder Unit'
    ]

    display_labels = [
        'Head', 'Core', 'Arms', 'Legs', 'FCS', 'Generator', 'Main Booster',
        'Back Booster', 'Side Booster', 'Overed Booster',
        'Right Arm Unit', 'Left Arm Unit', 'Right Back Unit',
        'Left Back Unit', 'Shoulder Unit'
    ]

    parts_info = []
    for i, (lookup_key, display_label) in enumerate(zip(lookup_keys, display_labels)):
        offset = LOCAL_PARTS_OFFSET + i * PART_ENTRY_SIZE
        part_id_bytes = block[offset:offset + PART_ENTRY_SIZE]

        if len(part_id_bytes) != 2:
            part_id_str = "<Invalid>"
            part_name = "<Invalid>"
        else:
            part_id_num = int.from_bytes(part_id_bytes, byteorder='big')
            part_id_str = f"{part_id_num:04d}"
            part_name = part_name_lookup.get(lookup_key, {}).get(
                part_id_str, f"Unknown ID {part_id_str}")

        parts_info.append({
            "category": display_label,
            "part_id": part_id_str,
            "part_name": part_name
        })

    return parts_info


def extract_tuning(block):
    LOCAL_TUNING_OFFSET = 0x126  # 0x26E - 0x148
    TUNING_SIZE = 32  # 0x20 bytes

    tuning_labels = [
        'en_output',
        'en_capacity',
        'kp_output',
        'load',
        'en_weapon_skill',
        'maneuverability',
        'firing_stability',
        'aim_precision',
        'lock_speed',
        'missile_lock_speed',
        'radar_refresh_rate',
        'ecm_resistance',
        'rectification_head',
        'rectification_core',
        'rectification_arm',
        'rectification_leg',
        'horizontal_thrust_main',
        'vertical_thrust',
        'horizontal_thrust_side',
        'horizontal_thrust_back',
        'quick_boost_main',
        'quick_boost_side',
        'quick_boost_back',
        'quick_boost_overed',
        'turning_ability',
        'stability_head',
        'stability_core',
        'stability_legs',
    ]

    tuning_values = {}
    for i, label in enumerate(tuning_labels):
        value = block[LOCAL_TUNING_OFFSET + i]
        tuning_values[label] = value  # Value should be in range 0-50

    return tuning_values


def save_schematic_block_as_ac4a(hex_block: bytes):
    """
    Saves a single schematic block to  'output/{schematic_name}_{designer_name}.ac4a' file.
    """
    sch_data = display_schematic_info(hex_block)
    schematic_name = sch_data['name']
    designer_name = sch_data['designer']
    output_path = f"output/{schematic_name}_{designer_name}.ac4a"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(hex_block)


def load_schematic_block_from_ac4a(file_path: str) -> bytes:
    """
    Loads a schematic block from a .ac4a file.
    Returns the raw bytes representing the schematic block.
    """
    with open(file_path, "rb") as f:
        return f.read()


def write_blocks_to_desdoc(desdoc_path, blocks, backup=True):
    """Overwrite the active schematic blocks in DESDOC.DAT, in slot order, with
    the given list of blocks. Does not change the active count. Backs up first
    by default. Returns a human-readable message."""
    FIRST_MARKER_OFFSET = 0x148

    backup_msg = backup_desdoc(desdoc_path) if backup else ""
    data = bytearray(load_file(desdoc_path))

    for i, block in enumerate(blocks):
        if len(block) != BLOCK_SIZE:
            raise ValueError(f"Block {i} must be {BLOCK_SIZE} bytes.")
        offset = FIRST_MARKER_OFFSET + i * BLOCK_SIZE
        if offset + BLOCK_SIZE > len(data):
            raise ValueError(f"Block {i} exceeds DESDOC.DAT size.")
        data[offset:offset + BLOCK_SIZE] = block

    save_file(desdoc_path, data)
    msg = f"Saved {len(blocks)} schematic(s) to {desdoc_path}."
    return f"{msg} {backup_msg}".strip()


def insert_schematic(ac4a_path, desdoc_path, backup=True):
    """Splice an .ac4a block into DESDOC.DAT and bump the active-schematic count.

    By default a fresh backup of DESDOC.DAT is made first (``.bak``/``.bak1``...).
    Returns a human-readable message describing the result.
    """
    SCHEMATIC_COUNT_OFFSET = 5
    FIRST_MARKER_OFFSET = 0x148

    backup_msg = backup_desdoc(desdoc_path) if backup else ""

    ac4a_data = load_file(ac4a_path)
    desdoc_data = bytearray(load_file(desdoc_path))

    current_count = desdoc_data[SCHEMATIC_COUNT_OFFSET]
    insertion_offset = FIRST_MARKER_OFFSET + (current_count * BLOCK_SIZE)

    if insertion_offset + BLOCK_SIZE > len(desdoc_data):
        raise ValueError("Not enough space to insert schematic.")

    desdoc_data[insertion_offset:insertion_offset +
                BLOCK_SIZE] = ac4a_data[:BLOCK_SIZE]
    desdoc_data[SCHEMATIC_COUNT_OFFSET] += 1

    save_file(desdoc_path, desdoc_data)

    msg = (f"Inserted schematic from {ac4a_path} into {desdoc_path} "
           f"(slot {current_count + 1}).")
    return f"{msg} {backup_msg}".strip()
