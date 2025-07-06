from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton
from ui.schematic_detail_widget import SchematicDetailWidget


class ImportPreviewDialog(QDialog):
    def __init__(self, schematic_data: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preview Schematic")
        self.setMinimumSize(600, 500)

        main_layout = QVBoxLayout()
        self.detail_widget = SchematicDetailWidget()
        self.detail_widget.update_with_data(schematic_data)

        main_layout.addWidget(self.detail_widget)

        button_layout = QHBoxLayout()
        self.cancel_button = QPushButton("Cancel")
        self.import_button = QPushButton("Import")

        self.cancel_button.clicked.connect(self.reject)
        self.import_button.clicked.connect(self.accept)

        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.import_button)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
