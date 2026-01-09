from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QProgressBar
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFontMetrics
import qtawesome as qta
from UI.Themes.papika_global_themes import PAPIKA_THEME


class PathAnalyzerThread(QThread):
    finished = Signal(dict)
    
    def __init__(self, path_str):
        super().__init__()
        self.path_str = path_str
    
    def run(self):
        try:
            path = Path(self.path_str)
            if not path.exists() or not path.is_dir():
                self.finished.emit({'folders': 0, 'files': 0, 'total_size': 0})
                return
            
            folder_count = 0
            file_count = 0
            total_size = 0
            
            try:
                for entry in path.iterdir():
                    if entry.is_dir():
                        folder_count += 1
                    elif entry.is_file():
                        file_count += 1
                        try:
                            total_size += entry.stat().st_size
                        except (PermissionError, OSError):
                            pass
            except (PermissionError, OSError):
                pass
            
            self.finished.emit({
                'folders': folder_count,
                'files': file_count,
                'total_size': total_size
            })
        except Exception as e:
            print(f"Error analyzing path {self.path_str}: {e}")
            self.finished.emit({'folders': 0, 'files': 0, 'total_size': 0})


class SidebarNavigationDetailsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = None
        self.analyzer_thread = None
        self.spacing = PAPIKA_THEME.get_spacing()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self.spacing['margins_medium'])
        layout.setSpacing(self.spacing['spacing_small'])
        
        self.path_label = QLabel("No path selected")
        self.path_label.setWordWrap(False)
        self.path_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.path_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(PAPIKA_THEME.get_sizes()['progress_bar_height'])
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        self.folders_label = QLabel("Folders: -")
        layout.addWidget(self.folders_label)
        
        self.files_label = QLabel("Files: -")
        layout.addWidget(self.files_label)
        
        self.size_label = QLabel("Total Size: -")
        layout.addWidget(self.size_label)
        
        self.loaded_label = QLabel("Loaded: -")
        layout.addWidget(self.loaded_label)
        
        layout.addStretch()
    
    def update_path(self, path_str):
        if not path_str or path_str == "network://":
            self.path_label.setText("No path selected")
            self.folders_label.setText("Folders: -")
            self.files_label.setText("Files: -")
            self.size_label.setText("Total Size: -")
            self.loaded_label.setText("Loaded: -")
            self.current_path = None
            return
        
        path = Path(path_str)
        if path.is_file():
            path = path.parent
        self.current_path = str(path)
        self._set_elided_path()
        self.folders_label.setText("Folders: Analyzing...")
        self.files_label.setText("Files: Analyzing...")
        self.size_label.setText("Total Size: Analyzing...")
        self.progress_bar.setVisible(True)
        
        if self.analyzer_thread and self.analyzer_thread.isRunning():
            self.analyzer_thread.finished.disconnect()
            self.analyzer_thread.quit()
            self.analyzer_thread.wait()
        
        self.analyzer_thread = PathAnalyzerThread(self.current_path)
        self.analyzer_thread.finished.connect(self._update_stats)
        self.analyzer_thread.start()
    
    def _update_stats(self, stats):
        self.progress_bar.setVisible(False)
        folder_count = stats.get('folders', 0)
        file_count = stats.get('files', 0)
        total_size = stats.get('total_size', 0)
        
        self.folders_label.setText(f"Folders: {folder_count}")
        self.files_label.setText(f"Files: {file_count}")
        
        if total_size > 0:
            size_str = self._format_size(total_size)
            self.size_label.setText(f"Total Size: {size_str}")
        else:
            self.size_label.setText("Total Size: 0 B")
    
    def _format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def _set_elided_path(self):
        if not self.current_path:
            self.path_label.setText("No path selected")
            return
        fm = QFontMetrics(self.path_label.font())
        text = fm.elidedText(self.current_path, Qt.ElideMiddle, max(80, self.path_label.width()))
        self.path_label.setText(text)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_path:
            self._set_elided_path()

    def show_loading(self, is_loading):
        self.progress_bar.setVisible(is_loading)
    
    def update_loaded_count(self, loaded, total):
        if total > 0:
            self.loaded_label.setText(f"Loaded: {loaded}/{total}")
        else:
            self.loaded_label.setText("Loaded: -")
