"""ac4db-style listing card for the schematic list (Phase F).

Reproduces the site's ``SchematicCard``: a horizontal strip with the thumbnail on
the left and, on the right, a date row over an author | name row, separated by
dividers — all wrapped in the signature nested outer/inner border that turns teal
on hover. Used via ``QListWidget.setItemWidget``.
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QListWidget
from PySide6.QtCore import Qt, QSize

from ui.palette import PALETTE

# 2:1 ratio (same as the 256x128 source), sized to fit the left panel.
CARD_THUMB_W, CARD_THUMB_H = 130, 65


def _divider(orientation):
    line = QFrame()
    line.setFrameShape(orientation)
    line.setStyleSheet(f"color:{PALETTE['divider']}; background:{PALETTE['divider']};")
    if orientation == QFrame.Shape.VLine:
        line.setFixedWidth(1)
    else:
        line.setFixedHeight(1)
    return line


def _text(value, bright=False):
    lbl = QLabel(value)
    color = PALETTE["text_bright"] if bright else PALETTE["text"]
    lbl.setStyleSheet(f"color:{color}; background:transparent;")
    return lbl


class SchematicListWidget(QListWidget):
    """List whose item-widget cards track the viewport width.

    Item-widget geometry follows the item's sizeHint (not the viewport), so wide
    cards would otherwise force a horizontal scrollbar. Pin each item's sizeHint
    width to the viewport on every resize, and keep that scrollbar off.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_item_widths()

    def fit_item_widths(self):
        w = self.viewport().width()
        for i in range(self.count()):
            item = self.item(i)
            item.setSizeHint(QSize(w, item.sizeHint().height()))


class SchematicCard(QFrame):
    """Nested-border card: thumbnail | (date / author | name)."""

    def __init__(self, pixmap, name, designer, date_str, parent=None):
        super().__init__(parent)
        self.setObjectName("cardOuter")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(2, 2, 2, 2)

        self.inner = QFrame()
        self.inner.setObjectName("cardInner")
        outer.addWidget(self.inner)
        self._apply_styles(hover=False)

        row = QHBoxLayout(self.inner)
        row.setContentsMargins(6, 4, 6, 4)
        row.setSpacing(8)

        thumb = QLabel()
        thumb.setFixedSize(CARD_THUMB_W, CARD_THUMB_H)
        thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if pixmap is not None and not pixmap.isNull():
            thumb.setPixmap(pixmap.scaled(
                CARD_THUMB_W, CARD_THUMB_H,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        else:
            thumb.setText("(no thumb)")
        row.addWidget(thumb)
        row.addWidget(_divider(QFrame.Shape.VLine))

        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(3)
        # Author and name split their row equally (both stretch 1).
        names = QHBoxLayout()
        names.setSpacing(8)
        names.addWidget(_text(designer), 1)
        names.addWidget(_divider(QFrame.Shape.VLine))
        names.addWidget(_text(name, bright=True), 1)
        # Date half and names half get equal vertical stretch (no trailing
        # stretch), so the two halves around the divider are equal height.
        if date_str:
            col.addWidget(_text(date_str), 1)
            col.addWidget(_divider(QFrame.Shape.HLine))
        col.addLayout(names, 1)
        row.addLayout(col, 1)

    def _apply_styles(self, hover):
        outer_border = PALETTE["border_outer"]
        outer_bg = PALETTE["hover_pulse"] if hover else PALETTE["bg"]
        inner_border = PALETTE["accent_teal"] if hover else PALETTE["border_inner"]
        self.setStyleSheet(
            f"#cardOuter {{ background:{outer_bg}; "
            f"border:2px solid {outer_border}; }}")
        self.inner.setStyleSheet(
            f"#cardInner {{ background:transparent; "
            f"border:2px solid {inner_border}; }}")

    # QSS parent-hover -> child-border doesn't reliably propagate, so drive the
    # hover swap from enter/leave events.
    def enterEvent(self, event):
        self._apply_styles(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_styles(hover=False)
        super().leaveEvent(event)
