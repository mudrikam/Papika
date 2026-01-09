import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget

from Configs.configs_file_manager import load_config


class SidebarActionDetailsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_directory = None
        self.previous_directory = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        title_label = QLabel('Directory Scan Information')
        title_label.setObjectName('action_details_title')
        title_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(title_label)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        self.path_label = QLabel('Path: -')
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)
        
        self.session_label = QLabel('Session: -')
        layout.addWidget(self.session_label)
        
        self.files_count_label = QLabel('Total Files: -')
        layout.addWidget(self.files_count_label)
        
        self.images_count_label = QLabel('Image Files: -')
        layout.addWidget(self.images_count_label)
        
        self.other_files_label = QLabel('Other Files: -')
        layout.addWidget(self.other_files_label)
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)
        
        self.last_scan_label = QLabel('Last Scan: -')
        layout.addWidget(self.last_scan_label)
        
        self.last_access_label = QLabel('Last Access: -')
        layout.addWidget(self.last_access_label)
        
        layout.addStretch()
    
    def _format_timestamp(self, timestamp_str: str) -> str:
        if not timestamp_str or timestamp_str == '-':
            return '-'
        try:
            dt = datetime.fromisoformat(timestamp_str)
        except Exception:
            return timestamp_str
        now = datetime.now()
        diff = now - dt
        seconds = int(diff.total_seconds())
        minutes = seconds // 60
        hours = minutes // 60
        days = diff.days
        month = dt.strftime('%b')
        date_str = f"{month}/{dt.day}/{dt.strftime('%y')}"
        if seconds < 60:
            return f"now, on {date_str}"
        if minutes < 60:
            return f"{minutes}m ago, on {date_str}"
        if hours < 24:
            return f"{hours}h ago, on {date_str}"
        if days < 30:
            return f"{days}d ago, on {date_str}"
        if days < 365:
            months = days // 30
            return f"{months}mo ago, on {date_str}"
        years = days // 365
        return f"{years}y ago, on {date_str}"
    
    def set_current_directory(self, directory_path: str):
        if self.current_directory and self.current_directory != directory_path:
            self._update_last_access(self.current_directory)
        
        self.previous_directory = self.current_directory
        self.current_directory = directory_path
        self.load_trails_data()
    
    def load_trails_data(self):
        if not self.current_directory:
            self._reset_labels()
            return
        
        directory_path = Path(self.current_directory)
        if not directory_path.exists() or not directory_path.is_dir():
            self._reset_labels()
            return
        
        try:
            base_path = Path(__file__).parent.parent.parent.parent
            configs = load_config(base_path)
            
            footprints_folder = directory_path / configs['database']['directory']
            trails_json_path = footprints_folder / 'papika_trails.json'
            
            if not trails_json_path.exists():
                self._reset_labels()
                return
            
            with open(trails_json_path, 'r', encoding='utf-8') as f:
                trails_data = json.load(f)
            
            self.path_label.setText(f"Path: {trails_data.get('path_folder', '-')}")
            self.session_label.setText(f"Session: {trails_data.get('folder_session_hash', '-')}")
            self.files_count_label.setText(f"Total Files: {trails_data.get('files_count', '-')}")
            self.images_count_label.setText(f"Image Files: {trails_data.get('detected_image_files', '-')}")
            self.other_files_label.setText(f"Other Files: {trails_data.get('other_files', '-')}")
            
            last_scan_formatted = self._format_timestamp(trails_data.get('last_scan', '-'))
            last_access_formatted = self._format_timestamp(trails_data.get('last_access', '-'))
            
            self.last_scan_label.setText(f"Last Scan: {last_scan_formatted}")
            self.last_access_label.setText(f"Last Access: {last_access_formatted}")
            
        except Exception as e:
            print(f"Error loading trails data: {e}")
            self._reset_labels()
    
    def _update_last_access(self, directory_path: str):
        if not directory_path:
            return
        
        dir_path = Path(directory_path)
        if not dir_path.exists() or not dir_path.is_dir():
            return
        
        try:
            base_path = Path(__file__).parent.parent.parent.parent
            configs = load_config(base_path)
            
            footprints_folder = dir_path / configs['database']['directory']
            trails_json_path = footprints_folder / 'papika_trails.json'
            
            if not trails_json_path.exists():
                return
            
            with open(trails_json_path, 'r', encoding='utf-8') as f:
                trails_data = json.load(f)
            
            trails_data['last_access'] = datetime.now().isoformat()
            
            with open(trails_json_path, 'w', encoding='utf-8') as f:
                json.dump(trails_data, f, indent=2)
        except Exception as e:
            print(f"Error updating last access: {e}")
    
    def closeEvent(self, event):
        if self.current_directory:
            self._update_last_access(self.current_directory)
        super().closeEvent(event)
    
    def update_from_scan_result(self, trails_data: dict):
        self.path_label.setText(f"Path: {trails_data.get('path_folder', '-')}")
        self.session_label.setText(f"Session: {trails_data.get('folder_session_hash', '-')}")
        self.files_count_label.setText(f"Total Files: {trails_data.get('files_count', '-')}")
        self.images_count_label.setText(f"Image Files: {trails_data.get('detected_image_files', '-')}")
        self.other_files_label.setText(f"Other Files: {trails_data.get('other_files', '-')}")
        
        last_scan_formatted = self._format_timestamp(trails_data.get('last_scan', '-'))
        last_access_formatted = self._format_timestamp(trails_data.get('last_access', '-'))
        
        self.last_scan_label.setText(f"Last Scan: {last_scan_formatted}")
        self.last_access_label.setText(f"Last Access: {last_access_formatted}")
    
    def _reset_labels(self):
        self.path_label.setText('Path: -')
        self.session_label.setText('Session: -')
        self.files_count_label.setText('Total Files: -')
        self.images_count_label.setText('Image Files: -')
        self.other_files_label.setText('Other Files: -')
        self.last_scan_label.setText('Last Scan: -')
        self.last_access_label.setText('Last Access: -')
