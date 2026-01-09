from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from UI.Themes.papika_global_themes import PAPIKA_THEME


class SidebarSettingsDetailsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setMinimumHeight(100)
        self.spacing = PAPIKA_THEME.get_spacing()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self.spacing['margins_medium'])
        layout.setSpacing(self.spacing['spacing_medium'])
        title = QLabel('Settings Info')
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet(PAPIKA_THEME.get_stylesheet_title())
        layout.addWidget(title)
        placeholder = QLabel('Placeholder: selected setting details will appear here')
        placeholder.setAlignment(Qt.AlignLeft)
        layout.addWidget(placeholder)
        layout.addStretch()
