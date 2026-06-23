"""Editable detail panel for a single schematic block.

Holds the current block, lets the user rename, swap/randomize parts, and
randomize colors/decals, and emits ``block_changed`` whenever the block is
mutated. The owning window stores the new block back and tracks dirty state.

A persistent header (thumbnail + name/designer/slot) stays visible above the
Parts / Tuning / Appearance tabs.
"""

from PySide6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox, QTreeWidget,
    QTreeWidgetItem, QScrollArea, QStyle, QFrame
)
from PySide6.QtCore import Qt, Signal

import util as st
from util import PART_SLOTS, COLOR_SECTION_NAMES, COLOR_CHANNEL_NAMES

_SWATCH_PX = 22
from ui.thumbnail import block_to_pixmap, THUMB_W, THUMB_H

_NAME_MAX_CHARS = 47  # (96-byte UTF-16-LE field // 2) - 1


class SchematicEditorWidget(QWidget):
    # Emitted whenever the user mutates the block; carries a short description
    # for status-bar feedback.
    block_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.block = None
        self._loading = False
        self._show_debug = False
        self.combos = []

        layout = QVBoxLayout(self)
        self._build_header(layout)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._build_parts_tab()
        self._build_tuning_tab()
        self._build_appearance_tab()

        self.clear()

    # --- construction ---------------------------------------------------
    def _build_header(self, layout):
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(THUMB_W, THUMB_H)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("border: 1px solid #555;")
        layout.addWidget(self.thumb_label, alignment=Qt.AlignmentFlag.AlignHCenter)

        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setMaxLength(_NAME_MAX_CHARS)
        self.name_edit.editingFinished.connect(self._on_name_edited)
        form.addRow("Name:", self.name_edit)
        self.designer_label = QLabel("-")
        form.addRow("Designer:", self.designer_label)
        self.slot_label = QLabel("-")
        form.addRow("User slot:", self.slot_label)
        layout.addLayout(form)

    def _build_parts_tab(self):
        outer = QWidget()
        ov = QVBoxLayout(outer)

        top = QHBoxLayout()
        self.debug_check = QCheckBox("Advanced: show debug parts")
        self.debug_check.toggled.connect(self._on_debug_toggled)
        top.addWidget(self.debug_check)
        top.addStretch()
        self.randomize_all_btn = QPushButton("Randomize all parts")
        self.randomize_all_btn.clicked.connect(self._randomize_all)
        top.addWidget(self.randomize_all_btn)
        ov.addLayout(top)

        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        for i, (_lookup_key, label) in enumerate(PART_SLOTS):
            grid.addWidget(QLabel(label), i, 0)
            combo = QComboBox()
            combo.currentIndexChanged.connect(
                lambda _idx, s=i: self._on_combo_changed(s))
            grid.addWidget(combo, i, 1)
            rb = QPushButton()
            # A style-drawn icon renders on every platform (an emoji glyph may not).
            rb.setIcon(self.style().standardIcon(
                QStyle.StandardPixmap.SP_BrowserReload))
            rb.setFixedWidth(40)
            rb.setToolTip(f"Randomize {label}")
            rb.clicked.connect(lambda _c, s=i: self._randomize_slot(s))
            grid.addWidget(rb, i, 2)
            self.combos.append(combo)
        grid.setColumnStretch(1, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(grid_host)
        ov.addWidget(scroll)
        self.tabs.addTab(outer, "Parts")

    def _build_tuning_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.tuning_tree = QTreeWidget()
        self.tuning_tree.setHeaderHidden(True)
        v.addWidget(self.tuning_tree)
        self.tabs.addTab(w, "Tuning")

    def _build_appearance_tab(self):
        w = QWidget()
        v = QVBoxLayout(w)
        self.rand_colors_btn = QPushButton("Randomize colors")
        self.rand_colors_btn.clicked.connect(self._randomize_colors)
        self.rand_decals_btn = QPushButton("Randomize decals")
        self.rand_decals_btn.clicked.connect(self._randomize_decals)
        v.addWidget(self.rand_colors_btn)
        v.addWidget(self.rand_decals_btn)

        v.addWidget(QLabel("Colors"))
        grid_host = QWidget()
        grid = QGridLayout(grid_host)
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(4)
        # Header row: a corner gap, then the 6 channel names.
        for c, name in enumerate(COLOR_CHANNEL_NAMES):
            header = QLabel(name)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(header, 0, c + 1)
        # One row per visible section: name label + 6 swatches.
        self.swatches = []  # [section][channel] -> QFrame
        for r, section_name in enumerate(COLOR_SECTION_NAMES):
            grid.addWidget(QLabel(section_name), r + 1, 0)
            row = []
            for c in range(len(COLOR_CHANNEL_NAMES)):
                sw = QFrame()
                sw.setFixedSize(_SWATCH_PX, _SWATCH_PX)
                sw.setFrameShape(QFrame.Shape.Box)
                grid.addWidget(sw, r + 1, c + 1)
                row.append(sw)
            self.swatches.append(row)
        grid.setColumnStretch(len(COLOR_CHANNEL_NAMES) + 1, 1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(grid_host)
        v.addWidget(scroll)
        self.tabs.addTab(w, "Appearance")

    # --- public API -----------------------------------------------------
    def load_block(self, block):
        self._loading = True
        try:
            self.block = block
            info = st.display_schematic_info(block)
            self.name_edit.setText(info["name"])
            self.designer_label.setText(info["designer"])
            self.slot_label.setText(str(info["category"]))
            self._set_thumbnail(block_to_pixmap(block))
            self._populate_combos(info)
            self._populate_tuning(info)
            self._populate_swatches()
            self.setEnabled(True)
        finally:
            self._loading = False

    def clear(self):
        self._loading = True
        self.block = None
        self.name_edit.clear()
        self.designer_label.setText("-")
        self.slot_label.setText("-")
        self._set_thumbnail(None)
        for combo in self.combos:
            combo.clear()
        self.tuning_tree.clear()
        self._clear_swatches()
        self.setEnabled(False)
        self._loading = False

    # --- helpers --------------------------------------------------------
    def _set_thumbnail(self, pixmap):
        if pixmap is None or pixmap.isNull():
            self.thumb_label.clear()
            self.thumb_label.setText("(no thumbnail)")
        else:
            self.thumb_label.setText("")
            self.thumb_label.setPixmap(pixmap)

    def _populate_combos(self, info=None):
        if info is None:
            info = st.display_schematic_info(self.block)
        pm = st.part_mapping
        was_loading = self._loading
        self._loading = True
        try:
            for i, (lookup_key, _label) in enumerate(PART_SLOTS):
                combo = self.combos[i]
                combo.clear()
                ids = [pid for pid in pm.get(lookup_key, {})
                       if self._show_debug or not pid.startswith("9")]
                ids.sort(key=lambda pid: pm[lookup_key][pid].lower())
                for pid in ids:
                    combo.addItem(f"{pm[lookup_key][pid]} ({pid})", pid)
                current_id = info["parts"][i]["part_id"]
                idx = combo.findData(current_id)
                if idx < 0:
                    # Current part not in the list (unknown / empty / debug-hidden):
                    # preserve it so selecting a slot never silently changes it.
                    combo.insertItem(
                        0, f"{info['parts'][i]['part_name']} ({current_id})", current_id)
                    idx = 0
                combo.setCurrentIndex(idx)
        finally:
            self._loading = was_loading

    def _select_combo_id(self, slot, pid):
        combo = self.combos[slot]
        was_loading = self._loading
        self._loading = True
        try:
            idx = combo.findData(pid)
            if idx < 0:
                name = st.part_mapping[PART_SLOTS[slot][0]].get(pid, pid)
                combo.insertItem(0, f"{name} ({pid})", pid)
                idx = 0
            combo.setCurrentIndex(idx)
        finally:
            self._loading = was_loading

    def _populate_tuning(self, info):
        self.tuning_tree.clear()
        for key, value in info["tuning"].items():
            QTreeWidgetItem(self.tuning_tree, [f"{key}: {value}"])

    def _populate_swatches(self):
        colors, _patterns, _eye = st.extract_color_data(self.block)
        sections = st.extract_visible_swatches(colors)
        for r, row in enumerate(sections):
            for c, (red, green, blue) in enumerate(row):
                self.swatches[r][c].setStyleSheet(
                    f"background-color: rgb({red}, {green}, {blue});")
                self.swatches[r][c].setToolTip(f"#{red:02X}{green:02X}{blue:02X}")

    def _clear_swatches(self):
        for row in self.swatches:
            for sw in row:
                sw.setStyleSheet("")
                sw.setToolTip("")

    # --- edit handlers --------------------------------------------------
    def _on_name_edited(self):
        if self._loading or self.block is None:
            return
        new_name = self.name_edit.text()
        if new_name == st.display_schematic_info(self.block)["name"]:
            return
        self.block = st.set_name_in_block(self.block, new_name)
        self.block_changed.emit(f"Renamed to '{new_name}'")

    def _on_combo_changed(self, slot):
        if self._loading or self.block is None:
            return
        pid = self.combos[slot].currentData()
        if pid is None:
            return
        self.block = st.set_part_in_block(self.block, slot, pid)
        self.block_changed.emit(f"Changed {PART_SLOTS[slot][1]}")

    def _randomize_slot(self, slot):
        if self.block is None:
            return
        pid = st.random_part_id(
            st.part_mapping, PART_SLOTS[slot][0], self._show_debug)
        if pid is None:
            return
        self.block = st.set_part_in_block(self.block, slot, pid)
        self._select_combo_id(slot, pid)
        self.block_changed.emit(f"Randomized {PART_SLOTS[slot][1]}")

    def _randomize_all(self):
        if self.block is None:
            return
        self.block = st.randomize_parts_in_block(
            self.block, include_debug=self._show_debug)
        self._populate_combos()
        self.block_changed.emit("Randomized all parts")

    def _on_debug_toggled(self, checked):
        self._show_debug = checked
        if self.block is not None:
            self._populate_combos()

    def _randomize_colors(self):
        if self.block is None:
            return
        colors, _patterns, _eye = st.extract_color_data(self.block)
        self.block = st.replace_color_data(
            self.block, new_colors=st.randomize_colors(colors))
        self._populate_swatches()
        self.block_changed.emit("Colors randomized (view in-game)")

    def _randomize_decals(self):
        if self.block is None:
            return
        self.block = st.replace_decal_data(
            self.block, st.generate_full_random_decal_data())
        self.block_changed.emit("Decals randomized (view in-game)")
