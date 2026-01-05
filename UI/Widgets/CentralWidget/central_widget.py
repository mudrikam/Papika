from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout
from UI.Widgets.CentralWidget.central_widget_manager import CentralWidgetManager


class CentralWidget(QWidget):
    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.setObjectName("central_widget")
        self.base_path = base_path
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.manager = CentralWidgetManager(base_path, parent=self)
        layout.addWidget(self.manager.get_file_pane())
        
        self.setLayout(layout)
