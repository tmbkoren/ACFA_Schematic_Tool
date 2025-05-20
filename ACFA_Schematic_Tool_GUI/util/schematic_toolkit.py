import os
import sys
import re
import shutil
import struct

BLOCK_SIZE = 24280
NAME_SIZE = 96  # 48 wchar_t = 96 bytes in UTF-16


def resource_path(relative_path):
    """
    Get the absolute path to a resource, works for dev and PyInstaller bundles.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def parse_part_mapping(file_path):
    file_path = resource_path(file_path)

    part_mapping = {}
    current_category = None
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            if line.endswith('):'):
                category_name, _ = line[:-2].rsplit('(', 1)
                current_category = category_name.strip()
                part_mapping[current_category] = {}
                continue
            if current_category and ' ' in line:
                part_id, part_name = line.split(' ', 1)
                part_mapping[current_category][part_id.strip()
                                               ] = part_name.strip()
    return part_mapping

def load_file(path):
    with open(path, "rb") as f:
        return f.read()


def save_file(path, data):
    with open(path, "wb") as f:
        f.write(data)


def backup_desdoc(desdoc_path):
    """
    Creates a backup of the DESDOC.DAT file.
    If desdoc.bak already exists, it appends a counter: desdoc.bak1, desdoc.bak2, etc.
    """
    base_path = desdoc_path
    counter = 0
    while True:
        suffix = f".bak{counter}" if counter else ".bak"
        backup_path = base_path + suffix
        if not os.path.exists(backup_path):
            shutil.copy2(desdoc_path, backup_path)
            print(f"Backup created: {backup_path}")
            break
        counter += 1

    return f'Backup created: {backup_path}'


def linear_utf16_clean_name_reader(data, start_offset, max_bytes=96):
    raw_field = data[start_offset:start_offset + max_bytes]
    try:
        decoded = raw_field.decode('utf-16-le', errors='ignore').strip('\x00')
        match = re.match(r'^[A-Za-z0-9 ]+', decoded)
        return match.group(0).strip() if match else "<Invalid UTF-16 Encoding>"
    except UnicodeDecodeError:
        return "<Invalid UTF-16 Encoding>"


def read_timestamp(data, offset):
    timestamp_bytes = data[offset:offset + 8]
    return struct.unpack(">Q", timestamp_bytes)[0]


def extract_active_schematic_blocks(file_path):
    data = load_file(file_path)
    schematic_count = data[5]
    first_marker_offset = 0x148
    return [data[first_marker_offset + i * BLOCK_SIZE:first_marker_offset + (i + 1) * BLOCK_SIZE]
            for i in range(schematic_count)]


def display_schematic_info(block, part_mapping):
    schematic_name = linear_utf16_clean_name_reader(block, 1, NAME_SIZE)
    designer_name = linear_utf16_clean_name_reader(
        block, 1 + NAME_SIZE, NAME_SIZE)
    timestamp = read_timestamp(block, 192)
    protect_category_byte = block[200]
    category = (protect_category_byte & 0b01111111) + 1
    parts = extract_parts(block, part_mapping)
    tuning = extract_tuning(block)

    return {
        "name": schematic_name,
        "designer": designer_name,
        "category": category,
        "timestamp": timestamp,
        "parts": parts,
        "tuning": tuning
    }


def extract_parts(block, part_name_lookup):
    LOCAL_PARTS_OFFSET = 0xD8
    PART_ENTRY_SIZE = 2
    lookup_keys = [
        'Head', 'Core', 'Arms', 'Legs', 'FCS', 'Generator', 'Main Booster',
        'Back Booster', 'Side Booster', 'Overed Booster',
        'Arm Unit', 'Arm Unit', 'Back Unit', 'Back Unit', 'Shoulder Unit'
    ]
    display_labels = [
        'Head', 'Core', 'Arms', 'Legs', 'FCS', 'Generator', 'Main Booster',
        'Back Booster', 'Side Booster', 'Overed Booster',
        'Right Arm Unit', 'Left Arm Unit', 'Right Back Unit', 'Left Back Unit', 'Shoulder Unit'
    ]

    parts_info = []
    for i, (lookup_key, display_label) in enumerate(zip(lookup_keys, display_labels)):
        offset = LOCAL_PARTS_OFFSET + i * PART_ENTRY_SIZE
        part_id_bytes = block[offset:offset + PART_ENTRY_SIZE]
        if len(part_id_bytes) == 2:
            part_id_num = int.from_bytes(part_id_bytes, byteorder='big')
            part_id_str = f"{part_id_num:04d}"
            part_name = part_name_lookup.get(lookup_key, {}).get(
                part_id_str, f"Unknown ID {part_id_str}")
        else:
            part_id_str = "<Invalid>"
            part_name = "<Invalid>"
        parts_info.append({"category": display_label,
                          "part_id": part_id_str, "part_name": part_name})
    return parts_info


def extract_tuning(block):
    LOCAL_TUNING_OFFSET = 0x126
    tuning_labels = [
        'en_output', 'en_capacity', 'kp_output', 'load', 'en_weapon_skill',
        'maneuverability', 'firing_stability', 'aim_precision', 'lock_speed', 'missile_lock_speed',
        'radar_refresh_rate', 'ecm_resistance', 'rectification_head', 'rectification_core',
        'rectification_arm', 'rectification_leg', 'horizontal_thrust_main', 'vertical_thrust',
        'horizontal_thrust_side', 'horizontal_thrust_back', 'quick_boost_main', 'quick_boost_side',
        'quick_boost_back', 'quick_boost_overed', 'turning_ability', 'stability_head',
        'stability_core', 'stability_legs'
    ]
    return {label: block[LOCAL_TUNING_OFFSET + i] for i, label in enumerate(tuning_labels)}


def save_schematic_block_as_ac4a(hex_block: bytes, part_mapping: dict, output_dir="output"):
    info = display_schematic_info(hex_block, part_mapping)
    filename = f"{info['name']}_{info['designer']}.ac4a"
    os.makedirs(output_dir, exist_ok=True)
    save_file(os.path.join(output_dir, filename), hex_block)


def load_schematic_block_from_ac4a(file_path):
    return load_file(file_path)


def insert_schematic(ac4a_path, desdoc_path):
    backup_msg = backup_desdoc(desdoc_path)
    ac4a_data = load_file(ac4a_path)
    desdoc_data = bytearray(load_file(desdoc_path))
    current_count = desdoc_data[5]
    insertion_offset = 0x148 + (current_count * BLOCK_SIZE)

    if insertion_offset + BLOCK_SIZE > len(desdoc_data):
        raise ValueError("Not enough space to insert schematic.")

    desdoc_data[insertion_offset:insertion_offset +
                BLOCK_SIZE] = ac4a_data[:BLOCK_SIZE]
    desdoc_data[5] += 1
    save_file(desdoc_path, desdoc_data)
    return f"Inserted schematic from {ac4a_path} into {desdoc_path}. {backup_msg}"
