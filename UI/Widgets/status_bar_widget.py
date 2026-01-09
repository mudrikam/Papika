from PySide6.QtWidgets import QStatusBar, QLabel
from UI.Themes.papika_global_themes import PAPIKA_THEME

class StatusBar(QStatusBar):
    def __init__(self, cfg: dict, development: bool):
        super().__init__()
        self.dev_label = None
        if development:
            self.dev_label = QLabel("Development!")
            self.dev_label.setStyleSheet("color: red; font-weight: bold;")
            self.addWidget(self.dev_label)
        self.status_label = QLabel("")
        self.addWidget(self.status_label, 1)
        version = cfg.get("version", "")
        self.version_label = QLabel(f"Version: {version}")
        self.addPermanentWidget(self.version_label)

    def set_version(self, version: str):
        self.version_label.setText(f"Version: {version}")

    def set_development(self, development: bool):
        if development and self.dev_label is None:
            self.dev_label = QLabel("Development!")
            self.dev_label.setStyleSheet("color: red; font-weight: bold;")
            self.insertWidget(0, self.dev_label)
        elif not development and self.dev_label is not None:
            self.removeWidget(self.dev_label)
            self.dev_label.deleteLater()
            self.dev_label = None

    def set_status(self, text: str):
        self.status_label.setText(text)

    def show_temporary(self, text: str, timeout: int = 0):
        self.showMessage(text, timeout)