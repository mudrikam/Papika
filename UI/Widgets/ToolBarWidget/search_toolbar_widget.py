from pathlib import Path
from PySide6.QtWidgets import QToolBar, QLineEdit
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal
import qtawesome as qta


class SearchToolbarWidget(QToolBar):
    search_requested = Signal(str)

    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        self.setMovable(False)
        self._create_actions()

    def _create_actions(self):
        self.search_field = QLineEdit(self)
        self.search_field.setPlaceholderText('Search...')
        self.search_field.returnPressed.connect(self._on_search)
        self.addWidget(self.search_field)

        clear_icon = qta.icon('fa6s.xmark')
        clear = QAction(clear_icon, 'Clear', self)
        clear.triggered.connect(self._on_clear)
        self.addAction(clear)

    def _on_search(self):
        query = self.search_field.text().strip()
        self.search_requested.emit(query)
        self._show_status(f'Search: {query}', 2000)

    def _on_clear(self):
        self.search_field.clear()
        self._show_status('Cleared', 1000)

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