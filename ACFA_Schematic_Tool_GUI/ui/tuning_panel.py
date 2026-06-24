"""ac4db-style tuning display (Phase F).

The single most recognizable ac4db element: each of the 28 tuning values is shown
as a 50-segment bar (``SegmentBar``), grouped into 7 sections laid out in two
columns, exactly as on the site (see docs/QT_STYLING_SPEC.md).
"""

from math import ceil

from PySide6.QtWidgets import (
    QWidget, QFrame, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel
)
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRectF, QSize

from ui.palette import PALETTE

# Section -> ordered tuning keys (port verbatim; order matters and maps to the
# 28 bytes at local 0x126).
_LEFT_SECTIONS = [
    ("Capacity", ["load", "en_output", "en_capacity", "kp_output"]),
    ("Attack", ["maneuverability", "firing_stability", "aim_precision", "en_weapon_skill"]),
    ("Acquisition", ["lock_speed", "missile_lock_speed", "radar_refresh_rate", "ecm_resistance"]),
    ("Primal Armor", ["rectification_head", "rectification_core", "rectification_arm", "rectification_leg"]),
]
_RIGHT_SECTIONS = [
    ("Boost", ["horizontal_thrust_main", "vertical_thrust", "horizontal_thrust_side", "horizontal_thrust_back"]),
    ("Special Boost", ["quick_boost_main", "quick_boost_back", "quick_boost_side", "quick_boost_overed"]),
    ("Control", ["stability_head", "stability_core", "stability_legs", "turning_ability"]),
]

_SEGMENTS = 50
_SEG_W = 6.8
_SEG_H = 12.0
_SEG_GAP = 1.0
# Abbreviations that should stay upper-cased when humanizing a key.
_ABBREV = {"en": "EN", "kp": "KP", "ecm": "ECM", "pa": "PA"}


def _humanize(key):
    return " ".join(_ABBREV.get(w, w.capitalize()) for w in key.split("_"))


class SegmentBar(QWidget):
    """A fixed-width row of 50 segments; the first ``value`` are filled green."""

    def __init__(self, value=0, parent=None):
        super().__init__(parent)
        self._value = value
        w = ceil(_SEGMENTS * _SEG_W + (_SEGMENTS - 1) * _SEG_GAP) + 1
        self.setFixedSize(int(w), int(_SEG_H) + 1)

    def sizeHint(self):
        return self.size()

    def set_value(self, value, label=""):
        self._value = max(0, min(_SEGMENTS, int(value)))
        self.setToolTip(f"{label}: {value}" if label else str(value))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        fill = QColor(PALETTE["tuning_fill"])
        border = QPen(QColor(PALETTE["segment_border"]))
        border.setWidth(1)
        for i in range(_SEGMENTS):
            x = i * (_SEG_W + _SEG_GAP)
            rect = QRectF(x, 0, _SEG_W, _SEG_H)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(fill if i < self._value else Qt.BrushStyle.NoBrush)
            if i < self._value:
                painter.drawRect(rect)
            painter.setPen(border)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect)


class TuningPanel(QWidget):
    """Two columns of section cards, each a stack of labelled segment bars."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bars = {}  # tuning key -> SegmentBar

        root = QHBoxLayout(self)
        root.setSpacing(10)
        root.addLayout(self._build_column(_LEFT_SECTIONS), 1)
        root.addLayout(self._build_column(_RIGHT_SECTIONS), 1)

    def _build_column(self, sections):
        col = QVBoxLayout()
        col.setSpacing(8)
        for title, keys in sections:
            col.addWidget(self._build_card(title, keys))
        col.addStretch()
        return col

    def _build_card(self, title, keys):
        card = QFrame()
        card.setObjectName("tuningCard")
        card.setStyleSheet(
            f"#tuningCard {{ background:{PALETTE['bg']}; "
            f"border:1px solid {PALETTE['border_inner']}; }}")
        v = QVBoxLayout(card)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(4)

        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet(
            f"color:{PALETTE['text_title']}; font-weight:600; background:transparent;")
        v.addWidget(title_lbl)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color:{PALETTE['divider']};")
        v.addWidget(divider)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(3)
        for row, key in enumerate(keys):
            name = QLabel(_humanize(key))
            name.setStyleSheet(
                f"color:{PALETTE['text']}; background:transparent;")
            bar = SegmentBar()
            self._bars[key] = bar
            grid.addWidget(name, row, 0)
            grid.addWidget(bar, row, 1, alignment=Qt.AlignmentFlag.AlignVCenter)
        grid.setColumnStretch(0, 1)
        v.addLayout(grid)
        return card

    def set_tuning(self, tuning):
        """Update every bar from a ``{key: value}`` dict."""
        for key, bar in self._bars.items():
            bar.set_value(tuning.get(key, 0), label=key)

    def clear(self):
        for bar in self._bars.values():
            bar.set_value(0)
