"""Decode a schematic block's thumbnail into a Qt QPixmap (read-only preview).

Bridges the root `util` Pillow-based decoder to Qt by going through raw RGBA bytes
(more reliable under PySide6 than PIL.ImageQt). Returns None for blank or
undecodable thumbnails so callers can show a placeholder.
"""

from PySide6.QtGui import QImage, QPixmap

from util import extract_thumbnail, bytes_to_image

THUMB_W, THUMB_H = 256, 128
_THUMBNAIL_SIZE = 0x4010
_HEADER_SIZE = 0x10


def block_to_pixmap(block):
    """Return a 256x128 QPixmap for the block's thumbnail, or None if it is blank
    (all-zero image data) or cannot be decoded."""
    try:
        raw = extract_thumbnail(block)
        if len(raw) != _THUMBNAIL_SIZE or not any(raw[_HEADER_SIZE:]):
            return None  # truncated or unset (blank) thumbnail
        image = bytes_to_image(raw).convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        # .copy() detaches from the temporary `data` buffer before it is freed.
        qimg = QImage(data, image.width, image.height,
                      QImage.Format.Format_RGBA8888).copy()
        return QPixmap.fromImage(qimg)
    except Exception:
        return None
