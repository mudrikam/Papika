from pathlib import Path
from PySide6.QtWidgets import QToolBar, QApplication
from PySide6.QtGui import QAction, QPalette
from PySide6.QtCore import Signal
import qtawesome as qta
from UI.Themes.papika_global_themes import PAPIKA_THEME


class SettingsToolbarWidget(QToolBar):
    reload_requested = Signal()

    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        self.setMovable(False)
        self.colors = PAPIKA_THEME.get_colors()
        self._create_actions()

    def _create_actions(self):
        prefs_icon = qta.icon('fa6s.sliders', color=self.colors['icon_base'])
        prefs = QAction(prefs_icon, 'Preferences', self)
        prefs.triggered.connect(lambda: self._show_status('Open Preferences', 1500))
        self.addAction(prefs)

        reload_icon = qta.icon('fa6s.arrows-rotate', color=self.colors['primary'])
        self.reload_action = QAction(reload_icon, 'Reload', self)
        self.reload_action.triggered.connect(self._on_reload)
        self.addAction(self.reload_action)

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