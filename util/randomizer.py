"""Part swapping and full part randomization for .ac4a files."""

import os
import random

from .io_utils import save_file
from .schematic import display_schematic_info, load_schematic_block_from_ac4a


def swap_part_in_ac4a_file(file_path, part_category, new_part_id):
    """
    Reads an .ac4a file, swaps a part, and saves it back to the same file.

    :param file_path: Path to the .ac4a schematic file.
    :param part_category: The category of the part to swap (e.g., 'Head', 'Core').
    :param new_part_id: The new part ID (as a string or int).
    """

    def _swap_part_in_block(block, part_category, new_part_id):
        # This is a helper function nested inside for self-containment.
        LOCAL_PARTS_OFFSET = 0xD8
        PART_ENTRY_SIZE = 2
        display_labels = [
            'Head', 'Core', 'Arms', 'Legs', 'FCS', 'Generator', 'Main Booster',
            'Back Booster', 'Side Booster', 'Overed Booster',
            'Right Arm Unit', 'Left Arm Unit', 'Right Back Unit',
            'Left Back Unit', 'Shoulder Unit'
        ]

        try:
            part_index = display_labels.index(part_category)
        except ValueError:
            raise ValueError(f"Invalid part category: {part_category}. Must be one of {display_labels}")

        offset = LOCAL_PARTS_OFFSET + part_index * PART_ENTRY_SIZE

        try:
            part_id_num = int(new_part_id)
        except ValueError:
            raise ValueError(f"Invalid part ID: {new_part_id}. Must be a number.")

        new_part_bytes = part_id_num.to_bytes(2, byteorder='big')

        mutable_block = bytearray(block)
        mutable_block[offset:offset + PART_ENTRY_SIZE] = new_part_bytes
        return bytes(mutable_block)

    # Main logic for the file-based swap
    print(f"--- Modifying {file_path} ---")

    # 1. Load the schematic block from the file
    try:
        original_block = load_schematic_block_from_ac4a(file_path)
        print("Original file loaded.")
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    # 2. Perform the swap in the loaded block
    modified_block = _swap_part_in_block(original_block, part_category, new_part_id)
    print(f"Swapped '{part_category}' to part ID {new_part_id}.")

    # 3. Save the modified block back to the original file
    save_file(file_path, modified_block)
    print(f"Successfully saved changes to {file_path}.")
    print("")


def randomize_schematic_parts(file_path, part_mapping, new_name=None):
    """
    Reads an .ac4a file, randomizes its core parts, optionally renames it,
    and saves it back to a new file, deleting the old one.
    Excludes debug parts (IDs starting with '9').

    :param file_path: Path to the .ac4a schematic file.
    :param part_mapping: The dictionary of all parts, loaded from the text file.
    :param new_name: An optional new name for the schematic.
    """
    LOCAL_PARTS_OFFSET = 0xD8
    PART_ENTRY_SIZE = 2
    NAME_OFFSET = 1
    NAME_SIZE = 96  # 48 wchar_t = 96 bytes in UTF-16

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

    try:
        original_block = load_schematic_block_from_ac4a(file_path)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return

    mutable_block = bytearray(original_block)
    print(f"--- Randomizing {file_path} ---")

    # Get original designer name for the new filename
    original_info = display_schematic_info(original_block)
    designer_name = original_info['designer']

    # Handle renaming if a new name is provided
    if new_name:
        if len(new_name) > (NAME_SIZE // 2) - 1:
            new_name = new_name[:(NAME_SIZE // 2) - 1]
            print(f"Warning: Name truncated to '{new_name}'")

        encoded_name = new_name.encode('utf-16-le')
        name_buffer = bytearray(NAME_SIZE)
        name_buffer[:len(encoded_name)] = encoded_name
        mutable_block[NAME_OFFSET:NAME_OFFSET + NAME_SIZE] = name_buffer
        print(f"  Renamed schematic to: {new_name}")

    for i, (lookup_key, display_label) in enumerate(zip(lookup_keys, display_labels)):
        part_id_list = [
            part_id for part_id in part_mapping.get(lookup_key, {}).keys()
            if not part_id.startswith('9')
        ]
        if not part_id_list:
            print(
                f"Warning: No valid parts found for category '{lookup_key}'. Skipping.")
            continue

        random_part_id_str = random.choice(part_id_list)
        random_part_id_num = int(random_part_id_str)
        offset = LOCAL_PARTS_OFFSET + i * PART_ENTRY_SIZE
        new_part_bytes = random_part_id_num.to_bytes(2, byteorder='big')
        mutable_block[offset:offset + PART_ENTRY_SIZE] = new_part_bytes
        part_name = part_mapping[lookup_key][random_part_id_str]
        print(f"  {display_label}: {random_part_id_str} ({part_name})")

    # Determine the output path
    if new_name:
        output_dir = os.path.dirname(file_path)
        new_filename = f"{new_name}.ac4a"
        output_path = os.path.join(output_dir, new_filename)
    else:
        output_path = file_path

    save_file(output_path, bytes(mutable_block))
    print(f"\nSuccessfully saved randomized schematic to {output_path}.")
    return output_path
