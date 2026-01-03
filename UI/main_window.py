from pathlib import Path
from PySide6.QtWidgets import QMainWindow

class MainWindow(QMainWindow):
    def __init__(self, base_path: Path):
        super().__init__()
        self.base_path = base_path
