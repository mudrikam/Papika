from pathlib import Path
from PySide6.QtWidgets import QToolBar, QLineEdit, QComboBox, QWidget, QSizePolicy
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt, Signal
import qtawesome as qta


class NavigationToolbarWidget(QToolBar):
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
        self._create_actions()

    def _create_actions(self):
        back_icon = qta.icon('fa6s.arrow-left')
        self.back_action = QAction(back_icon, 'Back', self)
        self.back_action.setToolTip('Back')
        self.back_action.triggered.connect(self._on_back)
        self.back_action.setEnabled(False)
        self.addAction(self.back_action)

        forward_icon = qta.icon('fa6s.arrow-right')
        self.forward_action = QAction(forward_icon, 'Forward', self)
        self.forward_action.setToolTip('Forward')
        self.forward_action.triggered.connect(self._on_forward)
        self.forward_action.setEnabled(False)
        self.addAction(self.forward_action)

        up_icon = qta.icon('fa6s.arrow-up')
        self.up_action = QAction(up_icon, 'Up', self)
        self.up_action.setToolTip('Up')
        self.up_action.triggered.connect(self._on_up)
        self.addAction(self.up_action)

        refresh_icon = qta.icon('fa6s.rotate')
        refresh = QAction(refresh_icon, 'Refresh', self)
        refresh.setToolTip('Refresh')
        refresh.triggered.connect(self._refresh)
        self.addAction(refresh)

        self.addSeparator()

        control_height = 28

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

        self.addSeparator()

        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText('Search...')
        self.search_field.setMaximumWidth(200)
        self.search_field.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.search_field.setFixedHeight(control_height)
        self.search_field.returnPressed.connect(self._on_search)
        self.addWidget(self.search_field)

        self.addSeparator()

        self.filter_combo = QComboBox(self)
        self.filter_combo.addItems(['All', 'Files', 'Folders', 'Images', 'Documents'])
        self.filter_combo.setToolTip('Filter')
        self.filter_combo.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.filter_combo.setFixedHeight(control_height)
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        self.addWidget(self.filter_combo)

        self.addSeparator()

        list_view_icon = qta.icon('fa6s.list')
        list_view = QAction(list_view_icon, 'List View', self)
        list_view.setToolTip('List View')
        list_view.triggered.connect(lambda: self._show_status('List View', 1500))
        self.addAction(list_view)

        grid_view_icon = qta.icon('fa6s.table-cells-large')
        grid_view = QAction(grid_view_icon, 'Grid View', self)
        grid_view.setToolTip('Grid View')
        grid_view.triggered.connect(lambda: self._show_status('Grid View', 1500))
        self.addAction(grid_view)

        detail_view_icon = qta.icon('fa6s.table-list')
        detail_view = QAction(detail_view_icon, 'Detail View', self)
        detail_view.setToolTip('Detail View')
        detail_view.triggered.connect(lambda: self._show_status('Detail View', 1500))
        self.addAction(detail_view)

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
        query = self.search_field.text()
        self._show_status(f'Search: {query}', 2000)

    def _on_path_entered(self):
        path = self.path_display.text().strip()
        if not path:
            return
        self.update_path(path)
        self.path_changed.emit(path)
        self._show_status(f'Navigated to {path}', 1500)

    def _on_filter_changed(self, text: str):
        self._show_status(f'Filter: {text}', 1500)

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