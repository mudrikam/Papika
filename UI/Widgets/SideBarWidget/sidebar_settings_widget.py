from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy
from PySide6.QtCore import Signal, Qt
from UI.Themes.papika_global_themes import PAPIKA_THEME


class SidebarSettingsWidget(QWidget):
    settings_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.spacing = PAPIKA_THEME.get_spacing()
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self.spacing['margins_medium'])
        layout.setSpacing(self.spacing['spacing_medium'])
        title = QLabel('Settings')
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet(PAPIKA_THEME.get_stylesheet_title())
        layout.addWidget(title)
        placeholder = QLabel('Placeholder: settings controls will appear here')
        placeholder.setAlignment(Qt.AlignLeft)
        layout.addWidget(placeholder)
        btn = QPushButton('Open Preferences')
        btn.setEnabled(False)
        layout.addWidget(btn)
        layout.addStretch()
