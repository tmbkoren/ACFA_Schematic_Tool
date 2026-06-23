"""Schematic thumbnail (256x128 DXT1/BC1 texture) extraction and encoding.

Encoding uses quicktex (a pure-wheel BC1 encoder) rather than Wand/ImageMagick,
so there is no system-library dependency and it bundles cleanly with PyInstaller.
Decoding uses Pillow by wrapping the raw DXT1 payload in a minimal DDS header.
"""

import io
import struct

from PIL import Image

from .constants import ACFA_THUMBNAIL_HEADER


def extract_thumbnail(schematic_block: bytes) -> bytes:
    """
    Extracts the thumbnail data from a given schematic block.

    The schematic block is a chunk of data representing one schematic
    from the DESDOC.DAT file. This function isolates and returns the
    raw thumbnail data from within that block.

    Args:
        schematic_block: A bytes object representing a single schematic block.

    Returns:
        A bytes object containing the full thumbnail data (header and image).
    """
    # The absolute start of the first schematic is 0x148.
    # The absolute start of the first thumbnail is 0x200C.
    # The local offset is the difference: 0x200C - 0x148 = 0x1EC4.
    THUMBNAIL_LOCAL_OFFSET = 0x1EC4

    # The total size of the thumbnail data is 0x4010 bytes
    # (0x10 header + 0x4000 image data).
    THUMBNAIL_SIZE = 0x4010

    # Slice the block to get the thumbnail data
    thumbnail_data = schematic_block[THUMBNAIL_LOCAL_OFFSET:
                                     THUMBNAIL_LOCAL_OFFSET + THUMBNAIL_SIZE]

    return thumbnail_data


def bytes_to_image(thumbnail_bytes: bytes) -> Image.Image:
    """
    Converts raw ACFA thumbnail bytes into a Pillow Image object.

    Args:
        thumbnail_bytes: The 16400 bytes (0x4010) of thumbnail data.

    Returns:
        A Pillow Image object.
    """
    if len(thumbnail_bytes) != 0x4010:
        raise ValueError("Thumbnail data must be 0x4010 bytes long.")

    # The actual image data starts after the 16-byte header.
    dxt1_data = thumbnail_bytes[0x10:]

    # We need to construct a valid DDS header to make this readable by Pillow.
    # DDS header is 128 bytes.
    dds_header = bytearray(128)
    struct.pack_into('<4sI', dds_header, 0, b'DDS ', 124)  # Magic, Size
    # Flags
    struct.pack_into('<I', dds_header, 8, 0x1 | 0x2 | 0x4 | 0x1000 | 0x80000)
    struct.pack_into('<I', dds_header, 12, 128)  # Height
    struct.pack_into('<I', dds_header, 16, 256)  # Width
    struct.pack_into('<I', dds_header, 20, 16384)  # LinearSize
    # PixelFormat Sub-structure
    struct.pack_into('<I', dds_header, 76, 32)  # PixelFormat Size
    struct.pack_into('<I', dds_header, 80, 0x4)  # PixelFormat Flags (FourCC)
    struct.pack_into('<4s', dds_header, 84, b'DXT1')  # FourCC
    # Caps
    struct.pack_into('<I', dds_header, 108, 0x1000)  # DDSCAPS_TEXTURE

    dds_data = bytes(dds_header) + dxt1_data

    # Use an in-memory buffer to read the DDS data
    buffer = io.BytesIO(dds_data)
    image = Image.open(buffer)
    return image


def image_to_bytes(image: Image.Image, level: int = 18) -> bytes:
    """
    Converts a Pillow Image object into raw ACFA thumbnail bytes (16-byte ACFA
    header + 16384 bytes of DXT1/BC1) using quicktex.

    Args:
        image: A 256x128 Pillow image.
        level: quicktex quality level 0-18 (higher = better, slower). Output size
               is fixed regardless of level.
    """
    # Imported lazily so the rest of the package loads without quicktex installed.
    from quicktex import RawTexture
    from quicktex.s3tc.bc1 import BC1Encoder

    if image.size != (256, 128):
        raise ValueError("Image must be 256x128 pixels.")

    raw = RawTexture.frombytes(image.convert("RGBA").tobytes(), 256, 128)
    encoder = BC1Encoder()
    encoder.set_level(level)
    dxt1_data = encoder.encode(raw).tobytes()

    expected_size = 16384
    if len(dxt1_data) != expected_size:
        raise RuntimeError(
            f"DXT1 compression produced unexpected size: {len(dxt1_data)} bytes. Expected {expected_size}.")

    # Prepend the constant 16-byte ACFA header
    return ACFA_THUMBNAIL_HEADER + dxt1_data


def replace_thumbnail(schematic_block: bytes, new_thumbnail_bytes: bytes) -> bytes:
    """
    Replaces the thumbnail data within a schematic block.

    Args:
        schematic_block: The original schematic block bytes.
        new_thumbnail_bytes: The new thumbnail data (must be 0x4010 bytes).

    Returns:
        A new schematic block bytes object with the thumbnail replaced.
    """
    if len(new_thumbnail_bytes) != 0x4010:
        raise ValueError("New thumbnail data must be 0x4010 bytes long.")

    THUMBNAIL_LOCAL_OFFSET = 0x1EC4
    THUMBNAIL_SIZE = 0x4010

    # Create a mutable copy and replace the thumbnail data
    mutable_block = bytearray(schematic_block)
    mutable_block[THUMBNAIL_LOCAL_OFFSET:THUMBNAIL_LOCAL_OFFSET +
                  THUMBNAIL_SIZE] = new_thumbnail_bytes

    return bytes(mutable_block)
