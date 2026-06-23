"""Low-level binary file helpers."""


def load_file(path):
    with open(path, "rb") as f:
        return f.read()


def save_file(path, data):
    with open(path, "wb") as f:
        f.write(data)


def hex_dump(data: bytes, width: int = 16) -> str:
    lines = []
    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]
        hex_part = ' '.join(f'{b:02X}' for b in chunk)
        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        lines.append(f'{offset:08X}  {hex_part:<{width*3}}  {ascii_part}')
    return '\n'.join(lines)
