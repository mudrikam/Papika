from PySide6.QtWidgets import QWidget, QVBoxLayout


class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("central_widget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
