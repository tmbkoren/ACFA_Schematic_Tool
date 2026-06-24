"""ac4db.org color tokens and the global Qt stylesheet (Phase F).

One source of truth for the dark, square-cornered, nested-border look ported from
ac4db.org. ``PALETTE`` holds the hex tokens (see docs/QT_STYLING_SPEC.md);
``build_stylesheet()`` string-formats them into app-wide QSS.
"""

PALETTE = {
    "bg": "#000000",
    "surface_alt": "#141414",
    "hover_pulse": "#303030",
    "border_outer": "#878c90",
    "border_inner": "#3b393c",
    "accent_teal": "#6f9fa1",
    "divider": "#808080",
    "text": "#a5a5a5",
    "text_title": "#979797",
    "text_bright": "#c9c9c9",
    "tuning_fill": "#31c936",
    "segment_border": "#6f6f6f",
}


def build_stylesheet():
    """Return the app-wide QSS string built from PALETTE."""
    p = PALETTE
    return f"""
    QWidget {{
        background-color: {p['bg']};
        color: {p['text']};
        font-size: 11pt;
    }}
    QMainWindow, QDialog {{ background-color: {p['bg']}; }}

    QLabel {{ background: transparent; color: {p['text']}; }}

    /* Buttons: nested-border treatment (single border in QSS), square, teal hover. */
    QPushButton {{
        background-color: {p['bg']};
        color: {p['text_bright']};
        border: 2px solid {p['border_outer']};
        border-radius: 0;
        padding: 5px 12px;
    }}
    QPushButton:hover {{
        background-color: {p['hover_pulse']};
        border-color: {p['accent_teal']};
        color: {p['text_bright']};
    }}
    QPushButton:pressed {{ background-color: {p['surface_alt']}; }}
    QPushButton:disabled {{
        color: #5a5a5a;
        border-color: {p['border_inner']};
    }}

    QLineEdit, QComboBox, QSpinBox {{
        background-color: {p['surface_alt']};
        color: {p['text_bright']};
        border: 1px solid {p['border_inner']};
        border-radius: 0;
        padding: 3px 5px;
        selection-background-color: {p['accent_teal']};
    }}
    QComboBox:hover, QLineEdit:hover {{ border-color: {p['accent_teal']}; }}
    QComboBox QAbstractItemView {{
        background-color: {p['surface_alt']};
        color: {p['text_bright']};
        border: 1px solid {p['border_outer']};
        selection-background-color: {p['accent_teal']};
        selection-color: {p['bg']};
    }}

    QListWidget {{
        background-color: {p['bg']};
        border: 1px solid {p['border_inner']};
        border-radius: 0;
        outline: 0;
    }}
    QListWidget::item {{
        color: {p['text']};
        border-bottom: 1px solid {p['border_inner']};
        padding: 2px;
    }}
    QListWidget::item:hover {{ background-color: {p['hover_pulse']}; }}
    QListWidget::item:selected {{
        background-color: {p['surface_alt']};
        color: {p['text_bright']};
        border: 2px solid {p['accent_teal']};
    }}

    QTabWidget::pane {{
        border: 1px solid {p['border_inner']};
        border-radius: 0;
        top: -1px;
    }}
    QTabBar::tab {{
        background-color: {p['bg']};
        color: {p['text_title']};
        border: 1px solid {p['border_inner']};
        border-radius: 0;
        padding: 6px 14px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        color: {p['text_bright']};
        border-color: {p['border_outer']};
        border-bottom-color: {p['accent_teal']};
    }}
    QTabBar::tab:hover {{ color: {p['text_bright']}; }}

    QMenuBar {{ background-color: {p['bg']}; color: {p['text']}; }}
    QMenuBar::item:selected {{ background-color: {p['hover_pulse']}; }}
    QMenu {{
        background-color: {p['surface_alt']};
        color: {p['text']};
        border: 1px solid {p['border_outer']};
    }}
    QMenu::item:selected {{
        background-color: {p['accent_teal']};
        color: {p['bg']};
    }}

    QCheckBox {{ background: transparent; color: {p['text']}; }}
    QTreeWidget, QTreeView {{
        background-color: {p['bg']};
        border: 1px solid {p['border_inner']};
        border-radius: 0;
    }}

    QScrollArea {{ border: 0; }}
    QStatusBar {{ background-color: {p['bg']}; color: {p['text_title']}; }}

    QToolTip {{
        background-color: {p['surface_alt']};
        color: {p['text_bright']};
        border: 1px solid {p['border_outer']};
    }}

    QSlider::groove:horizontal {{
        background: {p['surface_alt']};
        height: 4px;
    }}
    QSlider::handle:horizontal {{
        background: {p['accent_teal']};
        width: 12px;
        margin: -5px 0;
    }}
    """
