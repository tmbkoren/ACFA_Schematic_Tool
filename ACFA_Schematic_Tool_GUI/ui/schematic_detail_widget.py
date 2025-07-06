from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QTextEdit,
    QSpacerItem, QSizePolicy, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtGui import QFont


class SchematicDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.info_label = QLabel("No schematic selected.")
        self.info_label.setWordWrap(True)
        self.main_layout.addWidget(self.info_label)

        # Stretch placeholder to keep size consistent when empty
        self.spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding
        )
        self.main_layout.addItem(self.spacer)

    def update_with_data(self, data: dict):
        self.clear()

        title = f"<b>{data['name']}</b> by {data['designer']} (User Slot {data['category']})"
        self.info_label.setText(title)

        self.add_tree_section("Parts", data["parts"])
        self.add_tree_section("Tuning", data["tuning"])

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

        self.main_layout.insertWidget(self.main_layout.count() - 1, group)

    def clear(self):
        while self.main_layout.count() > 2:
            item = self.main_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        self.info_label.setText("No schematic selected.")
