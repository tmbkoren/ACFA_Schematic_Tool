import random

# Emblem hex structure:
# size: 84h
# byte 0 : type (0-2), we use 2 always since it represents custom emblem
# bytes 1-3: unknown, always 00 00 00
# then, an array of 16 layers, total size 80h (16 * 8 bytes each)
# each layer structure:
# byte 0 : angle (0-180 decimal)
# byte 1 : image id (see below for valid ids)
# img ids
# 0-20; 29 - 60; 69 - 88; 97 - 112; 121 - 144; 149 - 164; 173 - 188; 205 - 252
# byte 2 : color (0-7 decimal)
# byte 3 : width (1-127 decimal)
# byte 4 : height (1-127 decimal)
# byte 5 : x position (0-255 decimal)
# byte 6 : y position (0-255 decimal)
# byte 7 : flags
#   bit 0 - 3 : unknown, always 0
#   bit 4 : negative angle (0 or 1)
#   bit 5 : unknown, always 0
#   bit 6 : negative x (0 or 1)
#   bit 7 : negative y (0 or 1)

# max img id = 192(int) = 0xC0
# max color = 07(int) = 0x07
# each category has gap of 8 after end
# angle 2 flags : 0-180 && negative_angle 1 : 0-1
# width and height : 1 - 127
# x and y : 0 - 255
# negatuve x and negative y : 0 - 1

def parse_emblem_data(data: bytes):
    """
    Parses a 132-byte emblem data block into a structured dictionary.

    Args:
        data: A bytes object of length 132 (0x84).

    Returns:
        A dictionary containing the emblem's type and a list of 16 layers,
        with each layer's properties parsed into a human-readable format.
        Returns None if the data length is incorrect.
    """
    if len(data) != 132:
        raise ValueError(f"Invalid data length. Expected 132 bytes, got {len(data)}.")

    emblem_info = {
        'type': data[0],
        'unknown_header': data[1:4].hex(),
        'layers': []
    }

    layers_data = data[4:]
    
    for i in range(16):
        offset = i * 8
        layer_bytes = layers_data[offset:offset + 8]
        
        if len(layer_bytes) < 8:
            # Avoids index out of range if data is malformed
            continue

        flags = layer_bytes[7]
        
        layer_info = {
            'layer_index': i,
            'angle': layer_bytes[0],
            'image_id': layer_bytes[1],
            'color': layer_bytes[2],
            'width': layer_bytes[3],
            'height': layer_bytes[4],
            'x_position': layer_bytes[5],
            'y_position': layer_bytes[6],
            'flags': {
                'raw_byte': f"0x{flags:02x}",
                'negative_angle': bool((flags >> 4) & 1),
                'negative_x': bool((flags >> 6) & 1),
                'negative_y': bool((flags >> 7) & 1),
            }
        }
        emblem_info['layers'].append(layer_info)
        
    return emblem_info

def parse_paint_dat(file_path: str) -> list[bytes]:
    """
    Parses the PAINT.DAT file to extract existing emblem data blocks.

    Emblems start at offset 0x214. Each emblem is 132 bytes (0x84) long.
    There are 64 possible emblem slots. Parsing stops when an emblem's
    first byte is 0x00, indicating a non-existent emblem.

    Args:
        file_path: The absolute path to the PAINT.DAT file.

    Returns:
        A list of bytes objects, where each bytes object is a 132-byte
        emblem data block.
    """
    EMBLEM_START_OFFSET = 0x214
    EMBLEM_SIZE = 132  # 0x84 bytes
    NUM_EMBLEM_SLOTS = 64

    try:
        with open(file_path, "rb") as f:
            paint_data = f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"PAINT.DAT not found at {file_path}")

    emblems = []
    for i in range(NUM_EMBLEM_SLOTS):
        current_emblem_offset = EMBLEM_START_OFFSET + (i * EMBLEM_SIZE)
        
        # Ensure there's enough data to read at least the first byte of an emblem
        if current_emblem_offset >= len(paint_data):
            break

        # Check if the emblem exists (first byte is not 0x00)
        if paint_data[current_emblem_offset] == 0x00:
            break  # Stop parsing if a non-existent emblem is found

        # Extract the full emblem data block
        emblem_data = paint_data[current_emblem_offset:current_emblem_offset + EMBLEM_SIZE]
        
        # Ensure the extracted block is the correct size
        if len(emblem_data) == EMBLEM_SIZE:
            emblems.append(emblem_data)
        else:
            # This case should ideally not happen if the file is well-formed
            # and the previous length check passed, but good for robustness.
            print(f"Warning: Incomplete emblem data found at slot {i}. Skipping.")
            break # Stop if an incomplete emblem is found

    return emblems

def append_emblem_to_paint_dat(file_path: str, new_emblem_data: bytes):
    """
    Appends a new emblem to the PAINT.DAT file by replacing the first empty slot.

    Args:
        file_path: The absolute path to the PAINT.DAT file.
        new_emblem_data: A bytes object representing the new emblem (must be 132 bytes).

    Raises:
        ValueError: If new_emblem_data is not 132 bytes long.
        FileNotFoundError: If PAINT.DAT is not found.
        RuntimeError: If no empty emblem slot is found in PAINT.DAT.
    """
    EMBLEM_START_OFFSET = 0x214
    EMBLEM_SIZE = 132  # 0x84 bytes
    NUM_EMBLEM_SLOTS = 64

    if len(new_emblem_data) != EMBLEM_SIZE:
        raise ValueError(f"New emblem data must be {EMBLEM_SIZE} bytes long, got {len(new_emblem_data)}.")

    try:
        with open(file_path, "rb") as f:
            paint_data = bytearray(f.read())
    except FileNotFoundError:
        raise FileNotFoundError(f"PAINT.DAT not found at {file_path}")

    found_empty_slot = False
    for i in range(NUM_EMBLEM_SLOTS):
        current_emblem_offset = EMBLEM_START_OFFSET + (i * EMBLEM_SIZE)

        # Ensure there's enough space in the file for this slot
        if current_emblem_offset + EMBLEM_SIZE > len(paint_data):
            # If we run out of file before finding an empty slot, it's an issue
            raise RuntimeError("PAINT.DAT file is too short or corrupted, no space for new emblem.")

        # Check if the emblem slot is empty (first byte is 0x00)
        if paint_data[current_emblem_offset] == 0x00:
            # Replace the empty slot with the new emblem data
            paint_data[current_emblem_offset:current_emblem_offset + EMBLEM_SIZE] = new_emblem_data
            found_empty_slot = True
            break

    if not found_empty_slot:
        raise RuntimeError("No empty emblem slots found in PAINT.DAT. File is full.")

    # Save the modified PAINT.DAT file
    with open(file_path, "wb") as f:
        f.write(paint_data)

def generate_random_emblem(num_layers: int | None = None) -> bytes:
    """
    Generates a random 132-byte emblem data block adhering to game limitations.

    Args:
        num_layers: Optional. The number of layers to generate (1-16). If None,
                    a random number of layers will be generated.

    Returns:
        A bytes object representing a randomly generated emblem.
    """
    EMBLEM_SIZE = 132  # 0x84 bytes
    emblem_data = bytearray(EMBLEM_SIZE)

    # Header (4 bytes)
    emblem_data[0] = 0x02  # Type: custom emblem
    emblem_data[1:4] = bytes([0x00, 0x00, 0x00])  # Unknown, always 0

    # Valid image IDs from documentation
    valid_image_ids = []
    for r in [(0, 20), (29, 60), (69, 88), (97, 112), (121, 144), (149, 164), (173, 188), (205, 252)]:
        valid_image_ids.extend(range(r[0], r[1] + 1))

    if num_layers is None:
        actual_num_layers = random.randint(1, 16)
    elif 1 <= num_layers <= 16:
        actual_num_layers = num_layers
    else:
        raise ValueError("num_layers must be between 1 and 16, or None.")

    # Layers (8 bytes each)
    for i in range(actual_num_layers):
        layer_offset = 4 + (i * 8)

        # byte 0 : angle (0-180 decimal)
        emblem_data[layer_offset] = random.randint(0, 180)

        # byte 1 : image id
        emblem_data[layer_offset + 1] = random.choice(valid_image_ids)

        # byte 2 : color (0-7 decimal)
        emblem_data[layer_offset + 2] = random.randint(0, 7)

        # byte 3 : width (1-127 decimal)
        emblem_data[layer_offset + 3] = random.randint(1, 127)

        # byte 4 : height (1-127 decimal)
        emblem_data[layer_offset + 4] = random.randint(1, 127)

        # byte 5 : x position (0-255 decimal)
        emblem_data[layer_offset + 5] = random.randint(0, 255)

        # byte 6 : y position (0-255 decimal)
        emblem_data[layer_offset + 6] = random.randint(0, 255)

        # byte 7 : flags
        flags = 0
        # bit 0 - 3 : unknown, always 0
        # bit 4 : negative angle (0 or 1)
        flags |= (random.randint(0, 1) << 4)
        # bit 5 : unknown, always 0
        # bit 6 : negative x (0 or 1)
        flags |= (random.randint(0, 1) << 6)
        # bit 7 : negative y (0 or 1)
        flags |= (random.randint(0, 1) << 7)
        emblem_data[layer_offset + 7] = flags

    # Fill remaining layers with zeros if actual_num_layers < 16
    for i in range(actual_num_layers, 16):
        layer_offset = 4 + (i * 8)
        emblem_data[layer_offset:layer_offset + 8] = bytes([0] * 8)

    return bytes(emblem_data)
