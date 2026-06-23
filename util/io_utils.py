"""Low-level binary file helpers."""

import os
import shutil
import sys


def resource_path(relative_path):
    """Absolute path to a bundled resource, for dev and PyInstaller alike.

    Under a PyInstaller onefile build, data added with ``--add-data`` is
    unpacked to ``sys._MEIPASS``; in dev it resolves relative to the cwd.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)  # type: ignore[attr-defined]
    return os.path.join(os.path.abspath("."), relative_path)


def load_file(path):
    with open(path, "rb") as f:
        return f.read()


def save_file(path, data):
    with open(path, "wb") as f:
        f.write(data)


def backup_desdoc(desdoc_path):
    """Copy DESDOC.DAT to a fresh ``.bak``/``.bak1``/``.bak2``... never overwriting
    an existing backup. Returns a human-readable message."""
    counter = 0
    while True:
        suffix = f".bak{counter}" if counter else ".bak"
        backup_path = desdoc_path + suffix
        if not os.path.exists(backup_path):
            shutil.copy2(desdoc_path, backup_path)
            break
        counter += 1
    return f"Backup created: {backup_path}"


def hex_dump(data: bytes, width: int = 16) -> str:
    lines = []
    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f'{offset:08X}  {hex_part:<{width*3}}  {ascii_part}')
    return '\n'.join(lines)
