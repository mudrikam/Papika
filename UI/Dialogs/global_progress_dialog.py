from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import qtawesome as qta
from UI.Themes.papika_global_themes import PAPIKA_THEME


class GlobalProgressDialog(QDialog):
    cancel_requested = Signal()
    
    def __init__(self, parent=None, title="Processing", initial_message="Please wait..."):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        if parent and hasattr(parent, 'windowIcon'):
            self.setWindowIcon(parent.windowIcon())
        
        colors = PAPIKA_THEME.get_colors()
        sizes = PAPIKA_THEME.get_sizes()
        spacing = PAPIKA_THEME.get_spacing()
        
        layout = QVBoxLayout(self)
        layout.setSpacing(spacing['spacing_medium'])
        layout.setContentsMargins(*spacing['margins_medium'])
        
        self.message_label = QLabel(initial_message)
        self.message_label.setWordWrap(True)
        layout.addWidget(self.message_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedHeight(25)
        layout.addWidget(self.progress_bar)
        
        self.detail_label = QLabel("")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet(f"color: {colors['text_secondary']};")
        layout.addWidget(self.detail_label)
        
        self.cancel_button = QPushButton()
        self.cancel_button.setText("Cancel")
        self.cancel_button.setIcon(qta.icon('fa6s.xmark', color=colors['icon_base']))
        self.cancel_button.setFixedHeight(sizes['button_height'])
        self.cancel_button.clicked.connect(self._on_cancel_clicked)
        layout.addWidget(self.cancel_button)
        
        self._is_cancelled = False
    
    def update_progress(self, value, maximum=None):
        if maximum is not None:
            self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
    
    def set_message(self, message):
        self.message_label.setText(message)
    
    def set_detail(self, detail):
        self.detail_label.setText(detail)
    
    def set_title(self, title):
        self.setWindowTitle(title)
    
    def set_indeterminate(self, indeterminate=True):
        if indeterminate:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(0)
        else:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
    
    def enable_cancel(self, enabled=True):
        self.cancel_button.setEnabled(enabled)
    
    def hide_cancel(self):
        self.cancel_button.hide()
    
    def show_cancel(self):
        self.cancel_button.show()
    
    def is_cancelled(self):
        return self._is_cancelled
    
    def _on_cancel_clicked(self):
        self._is_cancelled = True
        self.cancel_requested.emit()
        self.reject()
    
    def reset(self):
        self._is_cancelled = False
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Cancel")
