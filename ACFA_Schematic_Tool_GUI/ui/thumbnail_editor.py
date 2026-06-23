"""Mini crop/zoom/squish editor to set a schematic thumbnail from any image.

Phase E: replaces Phase D's plain stretch-to-fit. The user pans and zooms an
arbitrary image behind a fixed 2:1 crop frame; the framed region is cropped and
resampled to 256x128. Independent horizontal/vertical zoom allows deliberate
squish/stretch; locking the aspect keeps it uniform.

Design (per the agreed plan): the pixmap item stays at identity transform, so
scene coords == source-image pixels. ALL zoom lives on the *view*
(``view.scale(sx, sy)``). The crop box is therefore just
``mapToScene(frame_viewport_rect)`` in source pixels, and a single PIL function
(crop + resize) produces BOTH the live preview and the committed image — WYSIWYG,
one code path. Out-of-frame area is black-padded to match the in-game look.
"""

from PIL import Image
from PySide6.QtWidgets import (
    QDialog, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QSlider, QCheckBox,
    QDialogButtonBox,
)
from PySide6.QtGui import QImage, QPixmap, QColor, QPen
from PySide6.QtCore import Qt, QRectF, QPointF

THUMB_W, THUMB_H = 256, 128

# Display size of the crop frame in the viewport (widget pixels). 2:1, scaled up
# from 256x128 for comfortable editing.
_FRAME_W, _FRAME_H = 384, 192

# Zoom slider range (percent of the base "cover" scale).
_ZOOM_MIN, _ZOOM_MAX, _ZOOM_DEFAULT = 25, 400, 100


def _pil_to_qpixmap(img):
    img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    # .copy() detaches the QImage from the temporary `data` buffer.
    qimg = QImage(data, img.width, img.height,
                  QImage.Format.Format_RGBA8888).copy()
    return QPixmap.fromImage(qimg)


class _CropView(QGraphicsView):
    """Graphics view that draws a fixed 2:1 crop frame overlay in viewport pixels
    and dims everything outside it."""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(
            QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Full repaints so the overlay never leaves trails during pan/zoom.
        self.setViewportUpdateMode(
            QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

    def frame_rect(self):
        """The crop frame rectangle in viewport (widget) pixels, centered."""
        cx = self.viewport().width() / 2
        cy = self.viewport().height() / 2
        return QRectF(cx - _FRAME_W / 2, cy - _FRAME_H / 2, _FRAME_W, _FRAME_H)

    def drawForeground(self, painter, rect):
        # resetTransform() lets us paint in viewport pixels regardless of the
        # view's scale/scroll — the classic fixed-overlay technique.
        painter.resetTransform()
        f = self.frame_rect()
        vp = QRectF(self.viewport().rect())
        # Dim the four regions around the frame.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 130))
        painter.drawRect(QRectF(vp.left(), vp.top(), vp.width(), f.top() - vp.top()))
        painter.drawRect(QRectF(vp.left(), f.bottom(), vp.width(), vp.bottom() - f.bottom()))
        painter.drawRect(QRectF(vp.left(), f.top(), f.left() - vp.left(), f.height()))
        painter.drawRect(QRectF(f.right(), f.top(), vp.right() - f.right(), f.height()))
        # Frame border.
        pen = QPen(QColor(255, 255, 255, 220))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(f)


class ThumbnailEditorDialog(QDialog):
    """Pan/zoom/squish a source image behind a 2:1 frame; returns a 256x128 crop.

    Use ``if dlg.exec() == QDialog.DialogCode.Accepted: img = dlg.get_result()``.
    ``get_result()`` returns a 256x128 RGBA Pillow image, or None if cancelled.
    """

    def __init__(self, source_image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set thumbnail from image")
        self._source = source_image.convert("RGBA")
        self._result = None
        self._syncing = False
        self._initialized = False

        w, h = self._source.width, self._source.height
        self.scene = QGraphicsScene(self)
        self.item = QGraphicsPixmapItem(_pil_to_qpixmap(self._source))
        self.item.setTransformationMode(
            Qt.TransformationMode.SmoothTransformation)
        self.scene.addItem(self.item)
        # Pad the scene rect so the image's own edges can pan under the centered
        # frame (otherwise a corner crop is impossible).
        self.scene.setSceneRect(-w, -h, 3 * w, 3 * h)

        self.view = _CropView(self.scene, self)
        self.view.setMinimumSize(_FRAME_W + 80, _FRAME_H + 80)
        self.view.horizontalScrollBar().valueChanged.connect(self._update_preview)
        self.view.verticalScrollBar().valueChanged.connect(self._update_preview)

        self.preview = QLabel()
        self.preview.setFixedSize(THUMB_W, THUMB_H)
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setStyleSheet("border: 1px solid #555; background: #000;")

        self.lock_check = QCheckBox("Lock aspect (uniform zoom)")
        self.lock_check.setChecked(True)
        self.lock_check.toggled.connect(self._on_lock_toggled)

        self.hzoom = self._make_zoom_slider()
        self.vzoom = self._make_zoom_slider()
        self.hzoom.valueChanged.connect(lambda v: self._on_zoom_changed("h", v))
        self.vzoom.valueChanged.connect(lambda v: self._on_zoom_changed("v", v))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        self._build_layout(buttons)

    # --- construction ---------------------------------------------------
    def _make_zoom_slider(self):
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(_ZOOM_MIN, _ZOOM_MAX)
        s.setValue(_ZOOM_DEFAULT)
        return s

    def _build_layout(self, buttons):
        root = QVBoxLayout(self)
        root.addWidget(QLabel("Drag to pan. Adjust zoom; uncheck Lock to squish/stretch."))

        body = QHBoxLayout()
        body.addWidget(self.view, 1)

        side = QVBoxLayout()
        side.addWidget(QLabel("Preview (256×128):"))
        side.addWidget(self.preview)
        side.addWidget(self.lock_check)
        form = QFormLayout()
        form.addRow("Zoom X:", self.hzoom)
        form.addRow("Zoom Y:", self.vzoom)
        side.addLayout(form)
        side.addStretch()
        body.addLayout(side)
        root.addLayout(body)
        root.addWidget(buttons)

    # --- geometry / rendering ------------------------------------------
    def _base_scale(self):
        """Scale at which the source 'covers' the frame (no black bars)."""
        w, h = self._source.width, self._source.height
        return max(_FRAME_W / w, _FRAME_H / h)

    def _apply_zoom(self, center_on=None):
        base = self._base_scale()
        sx = base * self.hzoom.value() / 100.0
        sy = base * self.vzoom.value() / 100.0
        if center_on is None:
            center_on = self.view.mapToScene(self.view.viewport().rect().center())
        self.view.resetTransform()
        self.view.scale(sx, sy)
        self.view.centerOn(center_on)
        self._update_preview()

    def _crop_box(self):
        f = self.view.frame_rect()
        tl = self.view.mapToScene(round(f.left()), round(f.top()))
        br = self.view.mapToScene(round(f.right()), round(f.bottom()))
        return (round(tl.x()), round(tl.y()), round(br.x()), round(br.y()))

    def _render_crop(self):
        """The single source of truth: crop the framed region and resample to
        256x128, black-padding anything outside the source image."""
        box = self._crop_box()
        cropped = self._source.crop(box).resize(
            (THUMB_W, THUMB_H), Image.Resampling.LANCZOS)
        out = Image.new("RGBA", (THUMB_W, THUMB_H), (0, 0, 0, 255))
        out.alpha_composite(cropped)
        return out

    def _update_preview(self):
        if not self._initialized:
            return
        self.preview.setPixmap(_pil_to_qpixmap(self._render_crop()))

    # --- handlers -------------------------------------------------------
    def _on_zoom_changed(self, axis, value):
        if self._syncing:
            return
        if self.lock_check.isChecked():
            self._syncing = True
            (self.vzoom if axis == "h" else self.hzoom).setValue(value)
            self._syncing = False
        self._apply_zoom()

    def _on_lock_toggled(self, checked):
        if checked:
            self._syncing = True
            self.vzoom.setValue(self.hzoom.value())
            self._syncing = False
            self._apply_zoom()

    def _accept(self):
        self._result = self._render_crop()
        self.accept()

    def get_result(self):
        return self._result

    # --- lifecycle ------------------------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        if not self._initialized:
            self._initialized = True
            w, h = self._source.width, self._source.height
            self._apply_zoom(center_on=QPointF(w / 2, h / 2))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_preview()
