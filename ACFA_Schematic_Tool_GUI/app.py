from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QFileDialog, QMessageBox, QDialog
)
from ui.schematic_detail_widget import SchematicDetailWidget
from ui.import_preview_dialog import ImportPreviewDialog
from util import schematic_toolkit as st
import os
import sys

part_mapping = st.parse_part_mapping("ACFA_PS3_US_PARTID_TO_PARTNAME.txt")


class SchematicViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ACFA Schematic Viewer")
        self.setAcceptDrops(True)

        self.blocks = []
        self.file_path = None

        main_layout = QVBoxLayout()

        self.label = QLabel(
            "Drag & drop a DESDOC.DAT or .ac4a file, or use the Select button:")
        self.label.setWordWrap(True)
        main_layout.addWidget(self.label)

        self.select_button = QPushButton("Select File")
        self.select_button.clicked.connect(self.open_file_dialog)
        main_layout.addWidget(self.select_button)

        viewer_layout = QHBoxLayout()

        self.schematic_list = QListWidget()
        self.schematic_list.currentRowChanged.connect(
            self.show_schematic_details)
        self.schematic_list.setVisible(False)
        viewer_layout.addWidget(self.schematic_list)

        self.detail_area = SchematicDetailWidget()
        viewer_layout.addWidget(self.detail_area)

        main_layout.addLayout(viewer_layout)
        self.setLayout(main_layout)

        self.imexport_layout = QHBoxLayout()

        self.import_button = QPushButton("Import .ac4a into Save")
        self.import_button.setVisible(False)
        self.import_button.clicked.connect(self.import_schematic)
        self.imexport_layout.addWidget(self.import_button)

        self.export_button = QPushButton("Export to .ac4a")
        self.export_button.setVisible(False)
        self.export_button.clicked.connect(self.export_schematic)
        self.imexport_layout.addWidget(self.export_button)

        main_layout.addLayout(self.imexport_layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.process_file(file_path)

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "All Files (*)")
        if path:
            self.process_file(path)

    def process_file(self, path):
        self.file_path = path
        _, ext = os.path.splitext(path)

        self.label.setText(f"Selected file: {path}")
        self.select_button.setText("Select Another File")

        self.schematic_list.clear()
        self.detail_area.clear()
        self.schematic_list.setVisible(False)
        self.blocks = []

        if ext.lower() == ".ac4a":
            block = st.load_schematic_block_from_ac4a(path)
            data = st.display_schematic_info(block, part_mapping)
            self.schematic_list.setVisible(False)
            self.detail_area.update_with_data(data)
            self.import_button.setVisible(False)
            self.export_button.setVisible(False)
        else:
            self.blocks = st.extract_active_schematic_blocks(path)
            self.schematic_list.clear()
            for block in self.blocks:
                info = st.display_schematic_info(block, part_mapping)
                self.schematic_list.addItem(
                    f"{info['name']} by {info['designer']}")
            self.schematic_list.setVisible(True)
            self.schematic_list.setCurrentRow(0)
            self.import_button.setVisible(True)
            self.export_button.setVisible(True)

    def show_schematic_details(self, index):
        if 0 <= index < len(self.blocks):
            data = st.display_schematic_info(self.blocks[index], part_mapping)
            self.detail_area.update_with_data(data)
        else:
            self.detail_area.clear()

    def import_schematic(self):
        ac4a_path, _ = QFileDialog.getOpenFileName(
            self, "Select .ac4a to import", "", "AC4A Files (*.ac4a)")
        if not ac4a_path:
            return

        try:
            block = st.load_schematic_block_from_ac4a(ac4a_path)
            data = st.display_schematic_info(block, part_mapping)

            dialog = ImportPreviewDialog(data, self)
            if dialog.exec() == QDialog.Accepted:
                msg = st.insert_schematic(ac4a_path, self.file_path)
                self.blocks = st.extract_active_schematic_blocks(
                    self.file_path)

                # Refresh schematic list
                self.schematic_list.clear()
                for block in self.blocks:
                    info = st.display_schematic_info(block, part_mapping)
                    self.schematic_list.addItem(
                        f"{info['name']} by {info['designer']}")
                self.schematic_list.setVisible(True)
                self.schematic_list.setCurrentRow(
                    self.schematic_list.count() - 1)

                self.label.setText(msg)
            else:
                self.label.setText("Import cancelled.")

        except Exception as e:
            self.label.setText(f"Import failed: {e}")

    def export_schematic(self):
        index = self.schematic_list.currentRow()
        if index < 0:
            return

        block = self.blocks[index]
        info = st.display_schematic_info(block, part_mapping)
        default_name = f"{info['name']}_{info['designer']}.ac4a"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Schematic", default_name, "ACFA Schematic (*.ac4a)")

        if output_path:
            with open(output_path, "wb") as f:
                f.write(block)
            QMessageBox.information(
                self, "Exported", f"Schematic saved to:\n{output_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SchematicViewer()
    viewer.resize(800, 600)
    viewer.show()
    sys.exit(app.exec())
