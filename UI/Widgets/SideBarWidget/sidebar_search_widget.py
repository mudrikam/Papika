from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy
from PySide6.QtCore import Signal, Qt
from UI.Themes.papika_global_themes import PAPIKA_THEME


class SidebarSearchWidget(QWidget):
    search_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.spacing = PAPIKA_THEME.get_spacing()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self.spacing['margins_medium'])
        layout.setSpacing(self.spacing['spacing_medium'])
        title = QLabel('Search')
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet(PAPIKA_THEME.get_stylesheet_title())
        layout.addWidget(title)
        self.input = QLineEdit()
        self.input.setPlaceholderText('Enter query...')
        layout.addWidget(self.input)
        btn = QPushButton('Search')
        btn.setEnabled(False)
        layout.addWidget(btn)
        placeholder = QLabel('Placeholder: search results will appear in the central view')
        placeholder.setAlignment(Qt.AlignLeft)
        layout.addWidget(placeholder)
        layout.addStretch()
