"""Part ID -> part name mapping, parsed from the bundled lookup table.

`part_mapping` is loaded at import time from `DEFAULT_PART_MAPPING_FILE`, resolved
relative to the current working directory (run notebooks/scripts from the repo
root). It is `{category: {part_id: part_name}}`.
"""

DEFAULT_PART_MAPPING_FILE = "ACFA_PS3_US_PARTID_TO_PARTNAME.txt"


def parse_part_mapping(file_path):
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


part_mapping = parse_part_mapping(DEFAULT_PART_MAPPING_FILE)
