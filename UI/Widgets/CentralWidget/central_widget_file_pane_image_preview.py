from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPixmap
from pathlib import Path


class ClickableLabel(QLabel):
    double_clicked = Signal(str)

    def mouseDoubleClickEvent(self, event):
        path = self.property('image_path')
        if path:
            self.double_clicked.emit(str(path))


class ImagePreviewOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet('background-color: rgba(0, 0, 0, 180);')

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(20, 20, 20, 20)
        self._layout.setSpacing(0)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet('background: transparent;')
        self._layout.addWidget(self.image_label, 1)
        self.current_index = -1
        self._current_pixmap = None
        self.setFocusPolicy(Qt.StrongFocus)
        # track parent's resize so overlay can adapt
        if parent is not None:
            parent.installEventFilter(self)
        self.setVisible(False)

    def show_image(self, image_path: str):
        p = Path(image_path)
        if not p.exists() or not p.is_file():
            return
        pix = QPixmap(str(p))
        if pix.isNull():
            return
        parent = self.parent()
        if parent and hasattr(parent, 'images'):
            for idx, img in enumerate(parent.images):
                if str(img) == str(p):
                    self.current_index = idx
                    break
                else:
                    self.current_index = -1
        # cover parent
        if parent is not None:
            self.setGeometry(parent.rect())
        self._current_pixmap = pix
        self._rescale_current_pixmap()
        self.raise_()
        self.setVisible(True)
        self.setFocus()

    def _rescale_current_pixmap(self):
        if not self._current_pixmap or self._current_pixmap.isNull():
            return
        available_w = max(50, self.width() - 40)
        available_h = max(50, self.height() - 40)
        scaled = self._current_pixmap.scaled(available_w, available_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)

    def show_image_by_index(self, index: int):
        parent = self.parent()
        if not parent or not hasattr(parent, 'images'):
            return
        if index < 0 or index >= len(parent.images):
            return
        self.show_image(str(parent.images[index]))

    def next_image(self):
        parent = self.parent()
        if not parent or not hasattr(parent, 'images'):
            return
        if self.current_index < 0:
            return
        nxt = self.current_index + 1
        if nxt < len(parent.images):
            self.show_image_by_index(nxt)

    def prev_image(self):
        parent = self.parent()
        if not parent or not hasattr(parent, 'images'):
            return
        if self.current_index < 0:
            return
        prv = self.current_index - 1
        if prv >= 0:
            self.show_image_by_index(prv)

    def hideEvent(self, event):
        if hasattr(self, 'image_label') and self.image_label:
            self.image_label.clear()
        self._current_pixmap = None
        super().hideEvent(event)

    def mousePressEvent(self, event):
        self.setVisible(False)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale_current_pixmap()

    def eventFilter(self, obj, event):
        if obj is self.parent() and event.type() == QEvent.Resize:
            self.setGeometry(self.parent().rect())
            if self.isVisible():
                self._rescale_current_pixmap()
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.setVisible(False)
            return
        if event.key() == Qt.Key_Right or event.key() == Qt.Key_Down:
            self.next_image()
            return
        if event.key() == Qt.Key_Left or event.key() == Qt.Key_Up:
            self.prev_image()
            return
        super().keyPressEvent(event)
