from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, QThread, Signal
import qtawesome as qta


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


class SidebarDetailsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = None
        self.analyzer_thread = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        
        self.path_label = QLabel("No path selected")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.path_label)
        
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
        
        layout.addStretch()
    
    def update_path(self, path_str):
        if not path_str or path_str == "network://":
            self.path_label.setText("No path selected")
            self.folders_label.setText("Folders: -")
            self.files_label.setText("Files: -")
            self.size_label.setText("Total Size: -")
            return
        
        self.current_path = path_str
        path = Path(path_str)
        
        if path.is_file():
            path = path.parent
            path_str = str(path)
        
        self.path_label.setText(str(path))
        self.folders_label.setText("Folders: Analyzing...")
        self.files_label.setText("Files: Analyzing...")
        self.size_label.setText("Total Size: Analyzing...")
        
        if self.analyzer_thread and self.analyzer_thread.isRunning():
            self.analyzer_thread.finished.disconnect()
            self.analyzer_thread.quit()
            self.analyzer_thread.wait()
        
        self.analyzer_thread = PathAnalyzerThread(path_str)
        self.analyzer_thread.finished.connect(self._update_stats)
        self.analyzer_thread.start()
    
    def _update_stats(self, stats):
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
