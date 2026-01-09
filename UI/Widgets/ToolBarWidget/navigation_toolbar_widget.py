from pathlib import Path
from PySide6.QtWidgets import QToolBar, QLineEdit, QComboBox, QSizePolicy, QApplication
from PySide6.QtGui import QAction, QPalette
from PySide6.QtCore import Qt, Signal, QTimer
import qtawesome as qta
from UI.Themes.papika_global_themes import PAPIKA_THEME


class NavigationToolbarWidget(QToolBar):
    navigate_back = Signal()
    navigate_forward = Signal()
    navigate_up = Signal()
    refresh_requested = Signal()
    path_changed = Signal(str)
    view_mode_changed = Signal(str)
    sort_changed = Signal(str)
    grid_width_changed = Signal(int)
    search_triggered = Signal(str)
    
    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        self.setMovable(False)
        self.history = []
        self.history_index = -1
        self._current_view = 'grid'
        self.colors = PAPIKA_THEME.get_colors()
        self.sizes = PAPIKA_THEME.get_sizes()
        self._create_actions()
        self._set_view_mode(self._current_view)

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

        self.addSeparator()

        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText('Search...')
        self.search_field.setMaximumWidth(200)
        self.search_field.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.search_field.setFixedHeight(control_height)
        self.search_field.returnPressed.connect(self._on_search)
        self._search_debounce_ms = 300
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(lambda: self.search_triggered.emit(self.search_field.text().strip()))
        self.search_field.textChanged.connect(self._on_search_text_changed)
        self.addWidget(self.search_field)

        self.addSeparator()

        self.sort_combo = QComboBox(self)
        self.sort_combo.addItems(['Name', 'Size', 'Date'])
        self.sort_combo.setToolTip('Sort by')
        self.sort_combo.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.sort_combo.setFixedHeight(control_height)
        self.sort_combo.currentTextChanged.connect(lambda text: self.sort_changed.emit(text))
        self.addWidget(self.sort_combo)

        self.grid_width_combo = QComboBox(self)
        self.grid_width_combo.addItems([str(i) for i in range(2, 21)])
        self.grid_width_combo.setCurrentText('6')
        self.grid_width_combo.setToolTip('Grid columns')
        self.grid_width_combo.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.grid_width_combo.setFixedHeight(control_height)
        self.grid_width_combo.currentTextChanged.connect(lambda text: self.grid_width_changed.emit(int(text)))
        self.addWidget(self.grid_width_combo)

        self.addSeparator()

        list_view_icon = qta.icon('fa6s.list', color=self.colors['primary'])
        self.list_view_action = QAction(list_view_icon, 'List View', self)
        self.list_view_action.setToolTip('List View')
        self.list_view_action.triggered.connect(lambda: self._set_view_mode('list'))
        self.addAction(self.list_view_action)

        grid_view_icon = qta.icon('fa6s.table-cells-large', color=self.colors['icon_inactive'])
        self.grid_view_action = QAction(grid_view_icon, 'Grid View', self)
        self.grid_view_action.setToolTip('Grid View')
        self.grid_view_action.triggered.connect(lambda: self._set_view_mode('grid'))
        self.addAction(self.grid_view_action)

        detail_view_icon = qta.icon('fa6s.table-list', color=self.colors['icon_inactive'])
        self.detail_view_action = QAction(detail_view_icon, 'Detail View', self)
        self.detail_view_action.setToolTip('Detail View')
        self.detail_view_action.triggered.connect(lambda: self._set_view_mode('details'))
        self.addAction(self.detail_view_action)

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

    def _on_search(self):
        if hasattr(self, '_search_timer') and self._search_timer.isActive():
            self._search_timer.stop()
        query = self.search_field.text().strip()
        self.search_triggered.emit(query)
        self._show_status(f'Search: {query}', 2000)

    def _on_search_text_changed(self, text: str):
        t = (text or '').strip()
        if not t:
            if hasattr(self, '_search_timer') and self._search_timer.isActive():
                self._search_timer.stop()
            self.search_triggered.emit('')
            return
        if hasattr(self, '_search_timer'):
            self._search_timer.start(self._search_debounce_ms)

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
        if add_to_history:
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            if not self.history or self.history[-1] != path:
                self.history.append(path)
                self.history_index = len(self.history) - 1
        self.path_display.setText(path)
        self._update_navigation_buttons()
    
    def _update_navigation_buttons(self):
        back_enabled = self.history_index > 0
        forward_enabled = self.history_index < len(self.history) - 1
        self.back_action.setEnabled(back_enabled)
        self.forward_action.setEnabled(forward_enabled)
        self.back_action.setIcon(qta.icon('fa6s.arrow-left', color=self.colors['primary'] if back_enabled else self.colors['icon_inactive']))
        self.forward_action.setIcon(qta.icon('fa6s.arrow-right', color=self.colors['primary'] if forward_enabled else self.colors['icon_inactive']))
        self.paste_action.setIcon(qta.icon('fa6s.clipboard', color=self.colors['primary'] if self.paste_action.isEnabled() else self.colors['icon_inactive']))
        self.clear_action.setIcon(qta.icon('fa6s.xmark', color=self.colors['primary'] if self.clear_action.isEnabled() else self.colors['icon_inactive']))
    
    def _set_view_mode(self, mode):
        self._current_view = mode
        
        self.list_view_action.setIcon(qta.icon('fa6s.list', 
            color=self.colors['primary'] if mode == 'list' else self.colors['icon_inactive']))
        self.grid_view_action.setIcon(qta.icon('fa6s.table-cells-large', 
            color=self.colors['primary'] if mode == 'grid' else self.colors['icon_inactive']))
        self.detail_view_action.setIcon(qta.icon('fa6s.table-list', 
            color=self.colors['primary'] if mode == 'details' else self.colors['icon_inactive']))
        
        self.view_mode_changed.emit(mode)
        self._show_status(f'{mode.capitalize()} View', 1500)
    
    def update_extensions(self, extensions):
        current = self.sort_combo.currentText()
        self.sort_combo.clear()
        self.sort_combo.addItems(['Name', 'Size', 'Date'])
        if extensions:
            for ext in extensions:
                self.sort_combo.addItem(ext.upper())
        if current:
            idx = self.sort_combo.findText(current)
            if idx >= 0:
                self.sort_combo.setCurrentIndex(idx)

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