from pathlib import Path
from PySide6.QtWidgets import QToolBar
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal
import qtawesome as qta


class ActionToolbarWidget(QToolBar):
    run_requested = Signal()
    stop_requested = Signal()

    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        self.setMovable(False)
        self._create_actions()

    def _create_actions(self):
        play_icon = qta.icon('fa6s.play')
        self.play_action = QAction(play_icon, 'Run', self)
        self.play_action.setToolTip('Run')
        self.play_action.triggered.connect(self._on_run)
        self.addAction(self.play_action)

        pause_icon = qta.icon('fa6s.pause')
        pause = QAction(pause_icon, 'Pause', self)
        pause.setToolTip('Pause')
        pause.triggered.connect(lambda: self._show_status('Paused', 1500))
        self.addAction(pause)

        stop_icon = qta.icon('fa6s.stop')
        self.stop_action = QAction(stop_icon, 'Stop', self)
        self.stop_action.setToolTip('Stop')
        self.stop_action.triggered.connect(self._on_stop)
        self.addAction(self.stop_action)

    def _on_run(self):
        self.run_requested.emit()
        self._show_status('Run requested', 1500)

    def _on_stop(self):
        self.stop_requested.emit()
        self._show_status('Stop requested', 1500)

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