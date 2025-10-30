import random

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
    # each layer starts with image, 84 bytes, identical to the emblem data structure
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
    # min value refers to part being smallest compared to the decal, max value refers to part being largest compared to decal
    # head default value: 3F D9 99 9A (1.7 approximately), min value: 42 48 00 00 (50 decimal), max value: 3F D9 99 9A (1.7 approximately)
    # core default value: 40 95 70 74 (4.669977 approximately), min value: 42 48 00 00 (50 decimal), max value: 3F D9 99 9A (1.7 approximately)
    # both arms default value: 40 BD B4 ED (5.928336 approximately), min value: 42 48 00 00 (50 decimal), max value: 3F D9 99 9A (1.7 approximately)
    # legs default value: 40 DA 9B ED (6.831534 approximately), min value: 42 48 00 00 (50 decimal), max value: 3F D9 99 9A (1.7 approximately)

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




