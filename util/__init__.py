"""ACFA schematic toolkit.

All functionality previously inlined in save_editor.ipynb's first cell now lives
here, split by concern. Import everything with ``from util import *`` (run from
the repo root so the part-mapping table resolves).
"""

from .constants import (
    BLOCK_SIZE,
    NAME_SIZE,
    ACFA_THUMBNAIL_HEADER,
    DECAL_PART_DATA,
)
from .io_utils import load_file, save_file, hex_dump, resource_path, backup_desdoc
from .part_data import (
    parse_part_mapping,
    part_mapping,
    load_part_mapping,
    get_part_mapping,
)
from .schematic import (
    linear_utf16_clean_name_reader,
    read_timestamp,
    format_timestamp,
    extract_active_schematic_blocks,
    display_schematic_info,
    extract_parts,
    extract_tuning,
    save_schematic_block_as_ac4a,
    load_schematic_block_from_ac4a,
    insert_schematic,
    write_blocks_to_desdoc,
)
from .colors import (
    extract_color_data, replace_color_data, randomize_colors,
    extract_visible_swatches, COLOR_SECTION_NAMES, COLOR_CHANNEL_NAMES,
)
from .emblems import (
    parse_emblem_data,
    parse_paint_dat,
    generate_random_emblem,
    append_emblem_to_paint_dat,
)
from .decals import (
    extract_decal_data,
    replace_decal_data,
    generate_random_decal_layer,
    biased_scale,
    generate_random_decal_layer_alt,
    generate_random_decal_section,
    generate_full_random_decal_data,
)
from .thumbnails import (
    extract_thumbnail,
    bytes_to_image,
    image_to_bytes,
    replace_thumbnail,
)
from .randomizer import (
    swap_part_in_ac4a_file,
    randomize_schematic_parts,
    set_part_in_block,
    set_name_in_block,
    random_part_id,
    randomize_parts_in_block,
    PART_SLOTS,
)

__all__ = [
    # constants
    "BLOCK_SIZE", "NAME_SIZE", "ACFA_THUMBNAIL_HEADER", "DECAL_PART_DATA",
    # io
    "load_file", "save_file", "hex_dump", "resource_path", "backup_desdoc",
    # part data
    "parse_part_mapping", "part_mapping", "load_part_mapping", "get_part_mapping",
    # schematic
    "linear_utf16_clean_name_reader", "read_timestamp", "format_timestamp",
    "extract_active_schematic_blocks", "display_schematic_info",
    "extract_parts", "extract_tuning", "save_schematic_block_as_ac4a",
    "load_schematic_block_from_ac4a", "insert_schematic", "write_blocks_to_desdoc",
    # colors
    "extract_color_data", "replace_color_data", "randomize_colors",
    "extract_visible_swatches", "COLOR_SECTION_NAMES", "COLOR_CHANNEL_NAMES",
    # emblems
    "parse_emblem_data", "parse_paint_dat", "generate_random_emblem",
    "append_emblem_to_paint_dat",
    # decals
    "extract_decal_data", "replace_decal_data", "generate_random_decal_layer",
    "biased_scale", "generate_random_decal_layer_alt",
    "generate_random_decal_section", "generate_full_random_decal_data",
    # thumbnails
    "extract_thumbnail", "bytes_to_image", "image_to_bytes", "replace_thumbnail",
    # randomizer
    "swap_part_in_ac4a_file", "randomize_schematic_parts",
    "set_part_in_block", "set_name_in_block", "random_part_id",
    "randomize_parts_in_block", "PART_SLOTS",
]
