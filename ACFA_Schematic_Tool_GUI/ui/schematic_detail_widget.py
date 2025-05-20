from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QTextEdit,
    QSpacerItem, QSizePolicy, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtGui import QFont


class SchematicDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.info_label = QLabel("No schematic selected.")
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        # Stretch placeholder to keep size consistent when empty
        self.spacer = QSpacerItem(
            0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding
        )
        self.layout.addItem(self.spacer)

    def update_with_data(self, data: dict):
        self.clear()

        title = f"<b>{data['name']}</b> by {data['designer']} (User Slot {data['category']})"
        self.info_label.setText(title)

        self.add_tree_section("Parts", data["parts"])
        self.add_tree_section("Tuning", data["tuning"])

    def add_section(self, title: str, content: str):
        group = QGroupBox(title)
        box_layout = QVBoxLayout()
        text = QTextEdit()
        text.setReadOnly(True)
        text.setFont(QFont("Courier New", 9))
        text.setPlainText(content)
        box_layout.addWidget(text)
        group.setLayout(box_layout)
        group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.layout.insertWidget(self.layout.count() - 1, group)


    def add_tree_section(self, title: str, entries: dict | list):
        group = QGroupBox(title)
        group.setCheckable(True)
        group.setChecked(True)
        group.setFlat(True)  # optional for a cleaner look

        inner_layout = QVBoxLayout()
        tree = QTreeWidget()
        tree.setHeaderHidden(True)
        tree.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

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
            self.layout.activate()

        group.toggled.connect(handle_toggle)

        self.layout.insertWidget(self.layout.count() - 1, group)

    def clear(self):
        while self.layout.count() > 2:
            item = self.layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()

        self.info_label.setText("No schematic selected.")
