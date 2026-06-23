from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox,
    QSpacerItem, QSizePolicy, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt

from ui.thumbnail import THUMB_W, THUMB_H


class SchematicDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Persistent header: thumbnail preview + title. These are never removed by
        # clear(); only the dynamic Parts/Tuning sections below are.
        self.thumb_label = QLabel()
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setFixedSize(THUMB_W, THUMB_H)
        self.thumb_label.setStyleSheet("border: 1px solid #555;")
        self.main_layout.addWidget(self.thumb_label,
                                   alignment=Qt.AlignmentFlag.AlignHCenter)

        self.info_label = QLabel("No schematic selected.")
        self.info_label.setWordWrap(True)
        self.main_layout.addWidget(self.info_label)

        # Stretch placeholder to keep size consistent when empty
        self.spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.main_layout.addItem(self.spacer)

        self.set_thumbnail(None)

    def update_with_data(self, data: dict, thumbnail=None):
        self.clear()
        self.set_thumbnail(thumbnail)

        title = f"<b>{data['name']}</b> by {data['designer']} (User Slot {data['category']})"
        self.info_label.setText(title)

        self.add_tree_section("Parts", data["parts"])
        self.add_tree_section("Tuning", data["tuning"])

    def set_thumbnail(self, pixmap):
        """Show a QPixmap, or a placeholder when None/blank."""
        if pixmap is None or pixmap.isNull():
            self.thumb_label.clear()  # drops any existing pixmap
            self.thumb_label.setText("(no thumbnail)")
        else:
            self.thumb_label.setText("")
            self.thumb_label.setPixmap(pixmap)

    def add_tree_section(self, title: str, entries: dict | list):
        group = QGroupBox(title)
        group.setCheckable(True)
        group.setChecked(True)
        group.setFlat(True)

        inner_layout = QVBoxLayout()
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        if isinstance(entries, dict):
            for key, val in entries.items():
                QTreeWidgetItem(tree, [f"{key}: {val}"])
        elif isinstance(entries, list):
            for item in entries:
                part_str = f"{item['category']}: {item['part_name']} (ID {item['part_id']})"
                QTreeWidgetItem(tree, [part_str])

        inner_layout.addWidget(tree)
        group.setLayout(inner_layout)

        # Handle expand/collapse by showing/hiding tree content
        def handle_toggle(checked):
            tree.setVisible(checked)
            self.main_layout.activate()

        group.toggled.connect(handle_toggle)

        # Insert just before the trailing spacer.
        self.main_layout.insertWidget(self.main_layout.count() - 1, group)

    def clear(self):
        # Persistent items are thumb_label (0), info_label (1) and the spacer
        # (last). Remove only the dynamic sections in between.
        while self.main_layout.count() > 3:
            item = self.main_layout.takeAt(2)
            if item.widget():
                item.widget().deleteLater()

        self.info_label.setText("No schematic selected.")
        self.set_thumbnail(None)
