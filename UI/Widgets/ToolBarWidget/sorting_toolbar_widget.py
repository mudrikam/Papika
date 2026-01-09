from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QPalette
from PySide6.QtWidgets import QApplication, QToolBar

import qtawesome as qta
from UI.Themes.papika_global_themes import PAPIKA_THEME


class SortingToolbarWidget(QToolBar):
    sort_requested = Signal(str)
    filter_requested = Signal(str)
    group_requested = Signal(str)

    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        self.setMovable(False)
        self.colors = PAPIKA_THEME.get_colors()
        self._create_actions()

    def _create_actions(self):
        sort_asc_icon = qta.icon('fa6s.arrow-down-a-z', color=self.colors['primary'])
        self.sort_asc_action = QAction(sort_asc_icon, 'Sort Ascending', self)
        self.sort_asc_action.setToolTip('Sort Ascending (A-Z)')
        self.sort_asc_action.triggered.connect(lambda: self._on_sort('ascending'))
        self.addAction(self.sort_asc_action)

        sort_desc_icon = qta.icon('fa6s.arrow-down-z-a', color=self.colors['primary'])
        self.sort_desc_action = QAction(sort_desc_icon, 'Sort Descending', self)
        self.sort_desc_action.setToolTip('Sort Descending (Z-A)')
        self.sort_desc_action.triggered.connect(lambda: self._on_sort('descending'))
        self.addAction(self.sort_desc_action)

        self.addSeparator()

        filter_icon = qta.icon('fa6s.filter', color=self.colors['primary'])
        self.filter_action = QAction(filter_icon, 'Filter', self)
        self.filter_action.setToolTip('Filter Items')
        self.filter_action.triggered.connect(self._on_filter)
        self.addAction(self.filter_action)

        group_icon = qta.icon('fa6s.layer-group', color=self.colors['primary'])
        self.group_action = QAction(group_icon, 'Group', self)
        self.group_action.setToolTip('Group Items')
        self.group_action.triggered.connect(self._on_group)
        self.addAction(self.group_action)

    def _on_sort(self, order: str):
        self.sort_requested.emit(order)
        self._show_status(f"Sort {order}", 1500)

    def _on_filter(self):
        self.filter_requested.emit('')
        self._show_status('Filter', 1500)

    def _on_group(self):
        self.group_requested.emit('')
        self._show_status('Group', 1500)

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
