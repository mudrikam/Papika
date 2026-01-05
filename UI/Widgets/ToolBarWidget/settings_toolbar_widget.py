from pathlib import Path
from PySide6.QtWidgets import QToolBar, QApplication
from PySide6.QtGui import QAction, QPalette
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
        self._determine_theme_colors()
        prefs_icon = qta.icon('fa6s.sliders', color=self._base_icon_color)
        prefs = QAction(prefs_icon, 'Preferences', self)
        prefs.triggered.connect(lambda: self._show_status('Open Preferences', 1500))
        self.addAction(prefs)

        reload_icon = qta.icon('fa6s.arrows-rotate', color=self._active_color)
        self.reload_action = QAction(reload_icon, 'Reload', self)
        self.reload_action.triggered.connect(self._on_reload)
        self.addAction(self.reload_action)

    def _determine_theme_colors(self):
        app = QApplication.instance()
        dark = True
        if app:
            wc = app.palette().color(QPalette.Window)
            lum = 0.299 * wc.red() + 0.587 * wc.green() + 0.114 * wc.blue()
            dark = lum < 128
        if dark:
            self._base_icon_color = '#FFFFFF'
            self._inactive_color = '#9CA3AF'
        else:
            self._base_icon_color = '#000000'
            self._inactive_color = '#6B7280'
        self._active_color = '#f7a128'

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