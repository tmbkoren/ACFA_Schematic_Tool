from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QTextEdit, QSpacerItem, QSizePolicy, QTreeWidget, QTreeWidgetItem
from PySide6.QtGui import QFont


class SchematicDetailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.info_label = QLabel("No schematic selected.")
        self.info_label.setWordWrap(True)
        self.layout.addWidget(self.info_label)

        # Stretch placeholder to keep size consistent
        self.spacer = QSpacerItem(
            0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.spacer)

    def update_with_data(self, data: dict):
        self.clear(preserve_placeholder=False)

        title = f"<b>{data['name']}</b> by {data['designer']} (User Slot {data['category']})"
        self.info_label.setText(title)

        # self.add_section("Timestamp", str(data["timestamp"]))

        # parts_text = "\n".join(
        #     f"{part['category']}: {part['part_name']} ({part['part_id']})"
        #     for part in data["parts"]
        # )
        # self.add_section("Parts", parts_text)

        # tuning_text = "\n".join(
        #     f"{label}: {value}" for label, value in data["tuning"].items()
        # )
        # self.add_section("Tuning", tuning_text)

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
        self.layout.insertWidget(self.layout.count() - 1, group)


    def add_tree_section(self, title: str, entries: dict | list):
        tree = QTreeWidget()
        tree.setHeaderHidden(True)

        parent = QTreeWidgetItem([title])
        tree.addTopLevelItem(parent)

        if isinstance(entries, dict):
            for key, val in entries.items():
                QTreeWidgetItem(parent, [f"{key}: {val}"])
        elif isinstance(entries, list):
            for item in entries:
                part_str = f"{item['category']}: {item['part_name']} (ID {item['part_id']})"
                QTreeWidgetItem(parent, [part_str])
        parent.setExpanded(True)

        self.layout.insertWidget(self.layout.count() - 1, tree)


    def clear(self, preserve_placeholder=True):
        # Keep the info_label (index 0) and spacer (last item)
        while self.layout.count() > 2:
            item = self.layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()


        self.info_label.setText("No schematic selected.")
