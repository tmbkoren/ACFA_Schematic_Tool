"""Part ID -> part name mapping, parsed from the bundled lookup table.

The module-level ``part_mapping`` (``{category: {part_id: part_name}}``) is loaded
**eagerly** at import when the table can be found, so notebook/GUI usage stays
unchanged. If the file is genuinely missing (e.g. a misconfigured packaged build),
it falls back to an empty dict rather than crashing on import; callers can then
point it at the right file with ``load_part_mapping(path)``.

To avoid stale value-imports, code that needs the mapping at call time should use
``get_part_mapping()`` rather than capturing ``part_mapping`` at import.
"""

import os

from .io_utils import resource_path

DEFAULT_PART_MAPPING_FILE = "ACFA_PS3_US_PARTID_TO_PARTNAME.txt"


def parse_part_mapping(file_path):
    """Parse a part-mapping table file into ``{category: {part_id: part_name}}``."""
    part_mapping = {}
    current_category = None

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line:
                continue  # Skip empty lines

            # Detect category header like 'Head (0):'
            if line.endswith('):'):
                category_name, category_id = line[:-2].rsplit('(', 1)
                current_category = category_name.strip()
                part_mapping[current_category] = {}
                continue

            if current_category is None:
                continue  # Skip any lines before first category

            # Split the line into part_id and part_name
            if ' ' in line:
                part_id, part_name = line.split(' ', 1)
                part_mapping[current_category][part_id.strip()
                                               ] = part_name.strip()

    return part_mapping


def _find_mapping_file(filename=DEFAULT_PART_MAPPING_FILE):
    """Return the first existing candidate path for the mapping table, or None.

    Tries, in order: the path as given, the PyInstaller/cwd resource path, the
    cwd, and the repo root relative to this package (so it works regardless of
    the launch directory)."""
    candidates = [
        filename,
        resource_path(filename),
        os.path.join(os.getcwd(), filename),
        os.path.join(os.path.dirname(__file__), os.pardir, filename),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def load_part_mapping(path=None):
    """(Re)load the module-level ``part_mapping``. Returns it.

    With no argument, searches the standard locations. Sets an empty dict if the
    file cannot be found."""
    global part_mapping
    resolved = path or _find_mapping_file()
    part_mapping = parse_part_mapping(resolved) if resolved else {}
    return part_mapping


def get_part_mapping():
    """Return the part mapping, attempting a (re)load if it is currently empty."""
    if not part_mapping:
        load_part_mapping()
    return part_mapping


# Eager load at import — keeps the table populated for notebook/GUI value-imports
# whenever it can be found; degrades to {} instead of raising if it cannot.
part_mapping = {}
load_part_mapping()
