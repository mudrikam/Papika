from pathlib import Path
from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal
import qtawesome as qta


class SettingsToolbarWidget(QToolBar):
    reload_requested = Signal()

    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        self.setMovable(False)
        self._create_actions()

    def _create_actions(self):
        prefs_icon = qta.icon('fa6s.sliders')
        prefs = QAction(prefs_icon, 'Preferences', self)
        prefs.triggered.connect(lambda: self._show_status('Open Preferences', 1500))
        self.addAction(prefs)

        reload_icon = qta.icon('fa6s.arrows-rotate')
        reload = QAction(reload_icon, 'Reload', self)
        reload.triggered.connect(self._on_reload)
        self.addAction(reload)

    def _on_reload(self):
        self.reload_requested.emit()
        self._show_status('Settings reloaded', 1500)

    def _show_status(self, text: str, timeout: int = 2000):
        parent = self.parentWidget()
        if parent is None:
            return
        sb = parent.statusBar()
        if sb is None:
            return
        if hasattr(sb, 'show_temporary'):
            sb.show_temporary(text, timeout)
        else:
            sb.showMessage(text, timeout)