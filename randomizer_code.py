# This is a temporary file containing the schematic randomizer code.
# Please copy and paste the contents of this file into a new cell
# in your `save_editor.ipynb` notebook.

import random
import os

def randomize_schematic_parts(file_path, part_mapping, new_name=None):
    """
    Reads an .ac4a file, randomizes its core parts, optionally renames it, 
    and saves the result. If a new name is provided, it saves to a new file, 
    otherwise it overwrites the original.
    Excludes debug parts (IDs starting with '9').

    :param file_path: Path to the .ac4a schematic file.
    :param part_mapping: The dictionary of all parts, loaded from the text file.
    :param new_name: An optional new name for the schematic.
    """
    # This function assumes that other necessary functions like 
    # `load_schematic_block_from_ac4a`, `save_file`, and `display_schematic_info` 
    # are already defined in the notebook.

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
            print(f"Warning: No valid parts found for category '{lookup_key}'. Skipping.")
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
        new_filename = f"{new_name}_{designer_name}.ac4a"
        output_path = os.path.join(output_dir, new_filename)
    else:
        output_path = file_path

    save_file(output_path, bytes(mutable_block))
    print(f"\nSuccessfully saved randomized schematic to {output_path}.")


# --- Example Usage for Randomizer ---

# Specify the file to randomize and the new name
ac4a_file_to_randomize = "output/Sbeu Tarakan_Vlabus.ac4a"
new_schematic_name = "Randomized AC"

# Check if the file exists
if os.path.exists(ac4a_file_to_randomize):
    # 1. Show the parts list *before* the change
    print("--- BEFORE RANDOMIZATION ---")
    before_block = load_schematic_block_from_ac4a(ac4a_file_to_randomize)
    before_info = display_schematic_info(before_block)
    designer_name = before_info['designer']  # Get designer name for verification
    print(f"Name: {before_info['name']}")
    for part in before_info['parts']:
        print(f"  {part['category']}: {part['part_id']} ({part['part_name']})")
    print("")

    # 2. Call the randomizer function with a new name
    randomize_schematic_parts(ac4a_file_to_randomize, part_mapping, new_name=new_schematic_name)
    print("")

    # 3. Construct the new file path and verify the changes
    new_file_path = os.path.join("output", f"{new_schematic_name}_{designer_name}.ac4a")
    
    print("--- AFTER RANDOMIZATION ---")
    if os.path.exists(new_file_path):
        after_block = load_schematic_block_from_ac4a(new_file_path)
        after_info = display_schematic_info(after_block)
        print(f"Name: {after_info['name']} (Saved to: {new_file_path})")
        for part in after_info['parts']:
            print(f"  {part['category']}: {part['part_id']} ({part['part_name']})")
    else:
        print(f"Error: New file not found at '{new_file_path}'")
else:
    print(f"Example file not found: {ac4a_file_to_randomize}")
    print("Please ensure the file exists, for example by running a cell that calls 'save_schematic_block_as_ac4a'.")