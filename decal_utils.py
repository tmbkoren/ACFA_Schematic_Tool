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


def randomize_decal_data() -> bytearray:
    """
    Creates a randomized sequence of decal data.

    Returns:
        A bytearray of size 0x19A0 with each byte set to a random value.
    """
    DECAL_DATA_SIZE = 0x19A0
    return bytearray(random.randint(0, 255) for _ in range(DECAL_DATA_SIZE))

