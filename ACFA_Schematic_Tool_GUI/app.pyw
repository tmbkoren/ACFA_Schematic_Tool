import os
import sys

# Make the repo root importable so `import util` (the canonical toolkit) resolves
# regardless of the launch directory. No-op in a frozen bundle, where util is
# already collected by PyInstaller.
if not getattr(sys, "frozen", False):
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)


def _running_under_wsl():
    if sys.platform != "linux":
        return False
    try:
        release = os.uname().release.lower()
    except AttributeError:
        release = ""
    return "microsoft" in release or "WSL_DISTRO_NAME" in os.environ


# WSLg's Wayland backend mishandles Qt popup windows: combo-box dropdowns detach
# into orphaned top-level windows that won't close. XWayland (xcb) is reliable, so
# prefer it under WSL via a fallback LIST: Qt tries xcb first and, if its plugin
# can't load (e.g. libxcb-cursor0 missing), falls back to wayland instead of
# aborting. A single "xcb" value would crash the app when the plugin is absent.
if _running_under_wsl():
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb;wayland")

import tempfile

import requests
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem, QFileDialog,
    QMessageBox, QDialog, QInputDialog
)
from PySide6.QtCore import QThread, QObject, Signal, Qt, QSettings
from PySide6.QtGui import QAction, QIcon

import util as st
from util import part_mapping
from gui_util import updater
from ui.schematic_editor_widget import SchematicEditorWidget
from ui.import_preview_dialog import ImportPreviewDialog
from ui.thumbnail import block_to_pixmap
from ui.palette import build_stylesheet
from ui.schematic_card import SchematicCard, SchematicListWidget

CURRENT_VERSION = "1.0.1"

# Placeholder for the app/window icon. Drop your icon file in the repo root (or
# update this name) and it will be picked up automatically. resource_path() makes
# it resolve both when run from source and inside the PyInstaller bundle — for the
# bundled build also add it to PyInstaller's --add-data (e.g.
# "ACFA_icon.png:." on Linux / "ACFA_icon.png;." on Windows). A .png or .ico works.
ICON_FILENAME = "ACFA_icon.png"

# The save file lives at a fixed sub-path under the emulator's data folder; only
# the emulator folder's name/location varies between setups. Auto-detect probes
# these folder names in the launch directory (RPCS3 setups commonly name it
# "EMULATOR" — e.g. the PCFA pack — or "rpcs3"), and the user can point us at the
# emulator folder explicitly via File ▸ Set Emulator Folder (persisted below).
SAVE_SUBPATH = os.path.join(
    "dev_hdd0", "home", "00000001", "savedata",
    "BLUS30187ASSMBLY064", "DESDOC.DAT"
)
EMULATOR_FOLDER_NAMES = ("EMULATOR", "rpcs3")


def _desdoc_under(emulator_root):
    """Full DESDOC.DAT path for a given emulator folder (the one holding dev_hdd0)."""
    return os.path.join(emulator_root, SAVE_SUBPATH)


class DownloadWorker(QObject):
    """Downloads an .ac4a payload off the UI thread."""
    finished = Signal(bytes)
    error = Signal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
            self.finished.emit(response.content)
        except requests.RequestException as e:
            self.error.emit(str(e))


class SchematicViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"ACFA Schematic Viewer v{CURRENT_VERSION}")
        self.setAcceptDrops(True)

        # Persists the user-chosen emulator folder (org/app names set in main()).
        self.settings = QSettings()

        # App icon: loads ICON_FILENAME if present, otherwise no-op (placeholder
        # until an icon is added).
        icon_path = st.resource_path(ICON_FILENAME)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.blocks = []
        self.file_path = None
        self.is_desdoc = False
        self._current_index = -1
        self._dirty = False
        self._download_thread = None
        self._download_worker = None
        self._thumb_cache = {}  # index -> QPixmap or None

        self._build_menu()
        self._build_central()
        self.statusBar().showMessage("Ready")

        self.check_for_desdoc()
        self.check_for_updates()

    # --- UI construction ------------------------------------------------
    def _build_menu(self):
        menu = self.menuBar()

        file_menu = menu.addMenu("&File")
        self.action_open = QAction("&Open File…", self)
        self.action_open.triggered.connect(self.open_file_dialog)
        file_menu.addAction(self.action_open)

        self.action_save = QAction("&Save to DESDOC (backup)", self)
        self.action_save.triggered.connect(self.save_to_desdoc)
        file_menu.addAction(self.action_save)

        self.action_revert = QAction("&Revert Unsaved Changes", self)
        self.action_revert.triggered.connect(self.revert_changes)
        file_menu.addAction(self.action_revert)

        self.action_export = QAction("&Export Selected to .ac4a…", self)
        self.action_export.triggered.connect(self.export_schematic)
        file_menu.addAction(self.action_export)

        self.action_import = QAction("&Import .ac4a into Save…", self)
        self.action_import.triggered.connect(self.import_schematic)
        file_menu.addAction(self.action_import)

        self.action_import_online = QAction("Import from ac4&db ID…", self)
        self.action_import_online.triggered.connect(self.import_from_online_id)
        file_menu.addAction(self.action_import_online)

        file_menu.addSeparator()
        action_exit = QAction("E&xit", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        help_menu = menu.addMenu("&Help")
        action_about = QAction("&About", self)
        action_about.triggered.connect(self._show_about)
        help_menu.addAction(action_about)

    def _build_central(self):
        central = QWidget()
        main_layout = QVBoxLayout(central)

        self.hint_label = QLabel(
            "Drag & drop a DESDOC.DAT or .ac4a file, or use Select File:")
        self.hint_label.setWordWrap(True)
        main_layout.addWidget(self.hint_label)

        select_row = QHBoxLayout()
        self.select_button = QPushButton("Select File")
        self.select_button.clicked.connect(self.open_file_dialog)
        select_row.addWidget(self.select_button)

        self.set_emulator_button = QPushButton("Set Emulator Folder")
        self.set_emulator_button.setToolTip(
            "Point at your emulator folder (the one containing 'dev_hdd0') to "
            "auto-load the save")
        self.set_emulator_button.clicked.connect(self.set_emulator_folder)
        select_row.addWidget(self.set_emulator_button)
        main_layout.addLayout(select_row)

        viewer_layout = QHBoxLayout()
        self.schematic_list = SchematicListWidget()
        self.schematic_list.currentRowChanged.connect(
            self.show_schematic_details)
        viewer_layout.addWidget(self.schematic_list, 1)

        self.editor = SchematicEditorWidget()
        self.editor.block_changed.connect(self._on_block_edited)
        viewer_layout.addWidget(self.editor, 2)
        main_layout.addLayout(viewer_layout)

        button_row = QHBoxLayout()
        self.save_button = QPushButton("Save to DESDOC")
        self.save_button.clicked.connect(self.save_to_desdoc)
        button_row.addWidget(self.save_button)

        self.revert_button = QPushButton("Revert")
        self.revert_button.setToolTip("Discard unsaved changes and reload from disk")
        self.revert_button.clicked.connect(self.revert_changes)
        button_row.addWidget(self.revert_button)

        self.import_button = QPushButton("Import .ac4a into Save")
        self.import_button.clicked.connect(self.import_schematic)
        button_row.addWidget(self.import_button)

        self.import_online_button = QPushButton("Import from ac4db ID")
        self.import_online_button.clicked.connect(self.import_from_online_id)
        button_row.addWidget(self.import_online_button)

        self.export_button = QPushButton("Export to .ac4a")
        self.export_button.clicked.connect(self.export_schematic)
        button_row.addWidget(self.export_button)
        main_layout.addLayout(button_row)

        self.setCentralWidget(central)
        self._set_actions_enabled(save_loaded=False, design_selected=False)

    def _set_actions_enabled(self, save_loaded, design_selected):
        """Enable/disable actions by state.

        ``save_loaded``  -> a DESDOC.DAT is open (insert/online import allowed).
        ``design_selected`` -> a schematic is selected (export allowed).
        """
        for w in (self.import_button, self.action_import,
                  self.import_online_button, self.action_import_online):
            w.setEnabled(save_loaded)
        for w in (self.export_button, self.action_export):
            w.setEnabled(design_selected)
        self._refresh_save_enabled()

    def _refresh_save_enabled(self):
        """Save-to-DESDOC needs an open DESDOC with unsaved edits; Revert just
        needs unsaved edits (works for .ac4a too)."""
        can_save = self.is_desdoc and self._dirty
        self.save_button.setEnabled(can_save)
        self.action_save.setEnabled(can_save)
        self.revert_button.setEnabled(self._dirty)
        self.action_revert.setEnabled(self._dirty)

    def _set_dirty(self, dirty):
        self._dirty = dirty
        base = f"ACFA Schematic Viewer v{CURRENT_VERSION}"
        self.setWindowTitle(base + (" *" if dirty else ""))
        self._refresh_save_enabled()

    # --- Startup helpers ------------------------------------------------
    def check_for_desdoc(self):
        """Try to auto-load the save: first a folder the user pointed us at, then
        the common emulator folder names in the launch directory."""
        candidates = []
        saved = self.settings.value("emulator_folder", "")
        if saved:
            candidates.append(saved)
        candidates += [os.path.join(".", name) for name in EMULATOR_FOLDER_NAMES]

        for root in candidates:
            desdoc_path = _desdoc_under(root)
            if os.path.exists(desdoc_path):
                self.process_file(desdoc_path)
                return

    def set_emulator_folder(self):
        """Let the user point at their emulator folder (the one containing
        dev_hdd0); the rest of the save path is fixed. Persists on success."""
        start_dir = self.settings.value("emulator_folder", "") or ""
        folder = QFileDialog.getExistingDirectory(
            self, "Select your emulator folder (the one containing 'dev_hdd0')",
            start_dir)
        if not folder:
            return

        desdoc_path = _desdoc_under(folder)
        if os.path.exists(desdoc_path):
            self.settings.setValue("emulator_folder", folder)
            self.process_file(desdoc_path)
        else:
            QMessageBox.warning(
                self, "Save not found",
                "No DESDOC.DAT was found under that folder.\n\n"
                "Pick the emulator folder that contains 'dev_hdd0'. "
                "The full path looked for was:\n\n" + desdoc_path)

    def check_for_updates(self):
        self.update_thread = QThread()
        self.update_worker = updater.UpdateWorker(CURRENT_VERSION)
        self.update_worker.moveToThread(self.update_thread)

        self.update_worker.update_found.connect(self.on_update_found)
        self.update_worker.error_occurred.connect(self.on_update_error)
        self.update_thread.started.connect(self.update_worker.run)
        self.update_thread.finished.connect(self.update_thread.deleteLater)

        self.update_thread.start()

    def on_update_found(self, release_info):
        updater.show_update_dialog(release_info, self)
        self.update_thread.quit()

    def on_update_error(self, error_message):
        print(f"Update check failed: {error_message}")
        self.update_thread.quit()

    def _show_about(self):
        QMessageBox.about(
            self, "About",
            f"ACFA Schematic Viewer v{CURRENT_VERSION}\n\n"
            "Viewer/editor for Armored Core: For Answer (PS3, US) designs.")

    # --- Drag & drop ----------------------------------------------------
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            self.process_file(url.toLocalFile())

    # --- File handling --------------------------------------------------
    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "All Files (*)")
        if path:
            self.process_file(path)

    def process_file(self, path):
        self.file_path = path
        _, ext = os.path.splitext(path)

        self.hint_label.setText(f"Loaded: {path}")
        self.select_button.setText("Select Another File")
        self.statusBar().showMessage(f"Loaded {os.path.basename(path)}")

        self.schematic_list.clear()
        self.editor.clear()
        self.blocks = []
        self._thumb_cache = {}
        self._current_index = -1
        self._set_dirty(False)

        if ext.lower() == ".ac4a":
            # Single design: still goes through the blocks/editor model so editing
            # is uniform; only export (not Save-to-DESDOC) applies.
            self.is_desdoc = False
            self.blocks = [st.load_schematic_block_from_ac4a(path)]
            self.schematic_list.setVisible(False)
            self._current_index = 0
            self.editor.load_block(self.blocks[0])
            self._set_actions_enabled(save_loaded=False, design_selected=True)
        else:
            self.is_desdoc = True
            self.blocks = st.extract_active_schematic_blocks(path)
            self.schematic_list.setVisible(True)
            self._refresh_list(select_last=False)
            self._set_actions_enabled(save_loaded=True, design_selected=True)

    def _pixmap_for(self, index):
        """Decode (and cache) the thumbnail QPixmap for a block index; may be None."""
        if index not in self._thumb_cache:
            self._thumb_cache[index] = block_to_pixmap(self.blocks[index])
        return self._thumb_cache[index]

    def _make_card(self, index):
        """Build an ac4db-style card widget for a block index."""
        info = st.display_schematic_info(self.blocks[index], part_mapping)
        date_str = st.format_timestamp(info.get("timestamp", 0))
        return SchematicCard(
            self._pixmap_for(index), info["name"], info["designer"], date_str)

    def _refresh_list(self, select_last=False):
        """Repopulate the schematic list (with ac4db cards) from self.blocks."""
        self.schematic_list.clear()
        self._thumb_cache = {}
        for i in range(len(self.blocks)):
            card = self._make_card(i)
            item = QListWidgetItem()
            item.setSizeHint(card.sizeHint())
            self.schematic_list.addItem(item)
            self.schematic_list.setItemWidget(item, card)
        self.schematic_list.fit_item_widths()
        if self.schematic_list.count():
            self.schematic_list.setCurrentRow(
                self.schematic_list.count() - 1 if select_last else 0)

    def show_schematic_details(self, index):
        if 0 <= index < len(self.blocks):
            self._current_index = index
            self.editor.load_block(self.blocks[index])
        else:
            self._current_index = -1
            self.editor.clear()

    def _on_block_edited(self, message=""):
        """The editor mutated the current block; store it back and mark dirty."""
        idx = self._current_index
        if not (0 <= idx < len(self.blocks)):
            return
        self.blocks[idx] = self.editor.block
        self._set_dirty(True)
        # A rename or thumbnail edit changes the row's card; rebuild it
        # (DESDOC view only).
        if self.is_desdoc and 0 <= idx < self.schematic_list.count():
            self._thumb_cache.pop(idx, None)  # invalidate stale cached pixmap
            item = self.schematic_list.item(idx)
            card = self._make_card(idx)
            item.setSizeHint(card.sizeHint())
            self.schematic_list.setItemWidget(item, card)
            self.schematic_list.fit_item_widths()
        if message:
            self.statusBar().showMessage(f"{message} — unsaved")

    def save_to_desdoc(self):
        if not (self.is_desdoc and self.file_path):
            return
        try:
            msg = st.write_blocks_to_desdoc(self.file_path, self.blocks)
        except Exception as e:
            self.statusBar().showMessage(f"Save failed: {e}")
            QMessageBox.critical(self, "Save Error", f"Save failed: {e}")
            return
        self._set_dirty(False)
        self.statusBar().showMessage(msg)

    def revert_changes(self):
        if not (self._dirty and self.file_path):
            return
        res = QMessageBox.question(
            self, "Revert changes",
            "Discard all unsaved changes and reload from disk?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res != QMessageBox.StandardButton.Yes:
            return
        row = self.schematic_list.currentRow() if self.is_desdoc else 0
        self.process_file(self.file_path)  # reloads from disk, clears dirty
        if self.is_desdoc and 0 <= row < self.schematic_list.count():
            self.schematic_list.setCurrentRow(row)
        self.statusBar().showMessage("Reverted to last saved state.")

    # --- Import / export ------------------------------------------------
    def _preview_and_insert(self, ac4a_path):
        """Preview a schematic and, if confirmed, insert it into the open save.

        Returns True if inserted. Raises on load/parse/insert failure."""
        block = st.load_schematic_block_from_ac4a(ac4a_path)
        data = st.display_schematic_info(block, part_mapping)

        dialog = ImportPreviewDialog(data, self, thumbnail=block_to_pixmap(block))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            self.statusBar().showMessage("Import cancelled.")
            return False

        msg = st.insert_schematic(ac4a_path, self.file_path)
        self.blocks = st.extract_active_schematic_blocks(self.file_path)
        self.schematic_list.setVisible(True)
        self._set_dirty(False)  # reloaded from disk
        self._refresh_list(select_last=True)
        self._set_actions_enabled(save_loaded=True, design_selected=True)
        self.statusBar().showMessage(msg)
        return True

    def _confirm_discard_edits(self):
        """Return True to proceed; warn first if there are unsaved edits."""
        if not self._dirty:
            return True
        res = QMessageBox.question(
            self, "Unsaved edits",
            "You have unsaved edits that will be lost by importing (the save is "
            "reloaded from disk afterwards). Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        return res == QMessageBox.StandardButton.Yes

    def import_schematic(self):
        if not self._confirm_discard_edits():
            return
        ac4a_path, _ = QFileDialog.getOpenFileName(
            self, "Select .ac4a to import", "", "AC4A Files (*.ac4a)")
        if not ac4a_path:
            return
        try:
            self._preview_and_insert(ac4a_path)
        except Exception as e:
            self.statusBar().showMessage(f"Import failed: {e}")
            QMessageBox.critical(self, "Import Error", f"Import failed: {e}")

    def import_from_online_id(self):
        if not self._confirm_discard_edits():
            return
        API_BASE_URL = "https://ac4db.org/api/schematics/"
        schematic_id, ok = QInputDialog.getText(
            self, "Import from Online Database", "Enter Schematic ID:")
        if not (ok and schematic_id):
            return

        self.statusBar().showMessage(f"Downloading schematic ID: {schematic_id}…")
        self.import_online_button.setEnabled(False)
        self.action_import_online.setEnabled(False)

        self._download_thread = QThread()
        self._download_worker = DownloadWorker(
            f"{API_BASE_URL}{schematic_id}/download")
        self._download_worker.moveToThread(self._download_thread)
        self._download_thread.started.connect(self._download_worker.run)
        self._download_worker.finished.connect(self._on_download_finished)
        self._download_worker.error.connect(self._on_download_error)
        self._download_thread.start()

    def _stop_download_thread(self):
        if self._download_thread is not None:
            self._download_thread.quit()
            self._download_thread.wait()
            self._download_thread = None
            self._download_worker = None
        # Re-enable per current state (online import needs a loaded save).
        save_loaded = bool(self.blocks)
        self.import_online_button.setEnabled(save_loaded)
        self.action_import_online.setEnabled(save_loaded)

    def _on_download_finished(self, content):
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ac4a") as f:
                temp_file_path = f.name
                f.write(content)
            self._preview_and_insert(temp_file_path)
        except Exception as e:
            self.statusBar().showMessage(f"Import failed: {e}")
            QMessageBox.critical(self, "Import Error", f"Import failed: {e}")
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            self._stop_download_thread()

    def _on_download_error(self, message):
        self.statusBar().showMessage(f"Download failed: {message}")
        QMessageBox.critical(self, "Download Error", f"Download failed: {message}")
        self._stop_download_thread()

    def export_schematic(self):
        index = self._current_index
        if index < 0 or index >= len(self.blocks):
            return
        block = self.blocks[index]
        info = st.display_schematic_info(block, part_mapping)
        default_name = f"{info['name']}_{info['designer']}.ac4a"
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Save Schematic", default_name, "ACFA Schematic (*.ac4a)")
        if output_path:
            with open(output_path, "wb") as f:
                f.write(block)
            self.statusBar().showMessage(f"Exported to {output_path}")
            QMessageBox.information(
                self, "Exported", f"Schematic saved to:\n{output_path}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Names give QSettings a stable, cross-platform storage location.
    app.setOrganizationName("tmbkoren")
    app.setApplicationName("ACFA_Schematic_Tool")
    app.setStyleSheet(build_stylesheet())

    if _running_under_wsl():
        # WSLg software-composites each popup as its own top-level window; the
        # default fade/animation makes combo-box and menu popups slow to open and
        # close. Disabling these (cosmetic) animations makes them snap instantly.
        for _effect in (Qt.UIEffect.UI_AnimateCombo, Qt.UIEffect.UI_AnimateMenu,
                        Qt.UIEffect.UI_FadeMenu, Qt.UIEffect.UI_AnimateTooltip,
                        Qt.UIEffect.UI_FadeTooltip):
            app.setEffectEnabled(_effect, False)

    if _running_under_wsl() and app.platformName().startswith("wayland"):
        print(
            "Note: running on the Wayland backend under WSL, where Qt dropdown "
            "popups can detach and fail to close. The xcb backend is reliable but "
            "needs several X libraries. Install them and relaunch (the app will "
            "then use xcb automatically):\n"
            "  sudo apt install -y libxcb-cursor0 libxkbcommon-x11-0 "
            "libxcb-icccm4 libxcb-keysyms1 libxcb-xkb1\n"
            "(Run with QT_DEBUG_PLUGINS=1 if it still falls back, to see which "
            "library is missing.)",
            file=sys.stderr,
        )

    viewer = SchematicViewer()
    viewer.resize(1200, 800)
    viewer.show()
    sys.exit(app.exec())
