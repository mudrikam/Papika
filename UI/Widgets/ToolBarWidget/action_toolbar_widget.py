from pathlib import Path
from PySide6.QtWidgets import QToolBar, QLineEdit, QSizePolicy, QApplication
from PySide6.QtGui import QAction, QPalette
from PySide6.QtCore import Signal
import qtawesome as qta
from UI.Themes.papika_global_themes import PAPIKA_THEME

class ActionToolbarWidget(QToolBar):
    navigate_back = Signal()
    navigate_forward = Signal()
    navigate_up = Signal()
    refresh_requested = Signal()
    path_changed = Signal(str)

    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        self.setMovable(False)
        self.history = []
        self.history_index = -1
        self.colors = PAPIKA_THEME.get_colors()
        self.sizes = PAPIKA_THEME.get_sizes()
        self._create_actions()

    def _create_actions(self):
        back_icon = qta.icon('fa6s.arrow-left', color=self.colors['icon_inactive'])
        self.back_action = QAction(back_icon, 'Back', self)
        self.back_action.setToolTip('Back')
        self.back_action.triggered.connect(self._on_back)
        self.back_action.setEnabled(False)
        self.addAction(self.back_action)

        forward_icon = qta.icon('fa6s.arrow-right', color=self.colors['icon_inactive'])
        self.forward_action = QAction(forward_icon, 'Forward', self)
        self.forward_action.setToolTip('Forward')
        self.forward_action.triggered.connect(self._on_forward)
        self.forward_action.setEnabled(False)
        self.addAction(self.forward_action)

        up_icon = qta.icon('fa6s.arrow-up', color=self.colors['primary'])
        self.up_action = QAction(up_icon, 'Up', self)
        self.up_action.setToolTip('Up')
        self.up_action.triggered.connect(self._on_up)
        self.addAction(self.up_action)

        refresh_icon = qta.icon('fa6s.rotate', color=self.colors['primary'])
        self.refresh_action = QAction(refresh_icon, 'Refresh', self)
        self.refresh_action.setToolTip('Refresh')
        self.refresh_action.triggered.connect(self._refresh)
        self.addAction(self.refresh_action)

        self.addSeparator()

        control_height = self.sizes['control_height']

        self.path_display = QLineEdit(self)
        self.path_display.setReadOnly(False)
        self.path_display.setText("")
        self.path_display.setPlaceholderText('Enter path...')
        self.path_display.setToolTip('Enter path and press Enter')
        self.path_display.setMinimumWidth(300)
        self.path_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.path_display.setFixedHeight(control_height)
        self.path_display.returnPressed.connect(self._on_path_entered)
        self.addWidget(self.path_display)

        paste_icon = qta.icon('fa6s.clipboard', color=self.colors['primary'])
        self.paste_action = QAction(paste_icon, 'Paste', self)
        self.paste_action.setToolTip('Paste from clipboard')
        self.paste_action.triggered.connect(self._on_paste)
        self.addAction(self.paste_action)

        clear_icon = qta.icon('fa6s.xmark', color=self.colors['primary'])
        self.clear_action = QAction(clear_icon, 'Clear', self)
        self.clear_action.setToolTip('Clear path')
        self.clear_action.triggered.connect(self._on_clear)
        self.addAction(self.clear_action)

    def _on_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            path = self.history[self.history_index]
            self.path_display.setText(path)
            self.navigate_back.emit()
            self.path_changed.emit(path)
            self._update_navigation_buttons()
            self._show_status('Back', 1500)
    
    def _on_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            path = self.history[self.history_index]
            self.path_display.setText(path)
            self.navigate_forward.emit()
            self.path_changed.emit(path)
            self._update_navigation_buttons()
            self._show_status('Forward', 1500)

    def _update_navigation_buttons(self):
        back_enabled = self.history_index > 0
        forward_enabled = self.history_index < len(self.history) - 1
        self.back_action.setEnabled(back_enabled)
        self.forward_action.setEnabled(forward_enabled)
        self.back_action.setIcon(qta.icon('fa6s.arrow-left', color=self.colors['primary'] if back_enabled else self.colors['icon_inactive']))
        self.forward_action.setIcon(qta.icon('fa6s.arrow-right', color=self.colors['primary'] if forward_enabled else self.colors['icon_inactive']))
    
    def _on_up(self):
        current_path = self.path_display.text()
        if current_path:
            parent = str(Path(current_path).parent)
            if parent != current_path:
                self.update_path(parent)
                self.navigate_up.emit()
                self.path_changed.emit(parent)
                self._show_status('Up', 1500)
    
    def _refresh(self):
        self.refresh_requested.emit()
        self._show_status('Refreshed', 1500)

    def _on_path_entered(self):
        path = self.path_display.text().strip()
        if not path:
            return
        self.update_path(path)
        self.path_changed.emit(path)
        self._show_status(f'Navigated to {path}', 1500)

    def _on_paste(self):
        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if not text:
            return
        if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1]
        self.path_display.setText(text)
        self._on_path_entered()
        self._show_status('Pasted from clipboard', 1500)

    def _on_clear(self):
        self.path_display.clear()
        self.path_changed.emit('')
        main_window = self.window()
        if main_window:
            central_widget = main_window.centralWidget()
            if central_widget and hasattr(central_widget, 'navigation'):
                central_widget.navigation.collapse_tree()
        self._show_status('Cleared', 1500)

    def set_path(self, path: str):
        self.path_display.setText(path)
    
    def update_path(self, path: str, add_to_history: bool = True):
        if add_to_history and path:
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            if not self.history or self.history[-1] != path:
                self.history.append(path)
                self.history_index = len(self.history) - 1
        self.path_display.setText(path)
        self._update_navigation_buttons()
    
    def _update_navigation_buttons(self):
        self.back_action.setEnabled(self.history_index > 0)
        self.forward_action.setEnabled(self.history_index < len(self.history) - 1)

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
