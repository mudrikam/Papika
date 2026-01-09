from pathlib import Path
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
import qtawesome as qta
from PapikaCore.papika_initiate_directory_scan import scan_directory

class SidebarActionWidget(QWidget):
    scan_completed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_directory = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        label = QLabel('Step 1 Scan Directory')
        label.setAlignment(Qt.AlignLeft)
        layout.addWidget(label)
        scan_directory_button = QPushButton('Scan Directory', self)
        scan_directory_button.setObjectName('scan_directory_button')
        scan_directory_button.setIcon(qta.icon('fa6s.folder-open'))
        scan_directory_button.setCursor(Qt.PointingHandCursor)
        scan_directory_button.setFixedHeight(36)
        scan_directory_button.clicked.connect(self._on_scan_directory_clicked)
        layout.addWidget(scan_directory_button)
        
        label2 = QLabel('Step 2 Generate Embedding')
        label2.setAlignment(Qt.AlignLeft)
        layout.addWidget(label2)
        generate_embedding_button = QPushButton('Generate Embedding', self)
        generate_embedding_button.setObjectName('generate_embedding_button')
        generate_embedding_button.setIcon(qta.icon('fa6s.wand-magic-sparkles'))
        generate_embedding_button.setCursor(Qt.PointingHandCursor)
        generate_embedding_button.setFixedHeight(36)
        layout.addWidget(generate_embedding_button)

        label3 = QLabel('Step 3 Generate Image Caption')
        label3.setAlignment(Qt.AlignLeft)
        layout.addWidget(label3)
        generate_caption_button = QPushButton('Generate Caption', self)
        generate_caption_button.setObjectName('generate_caption_button')
        generate_caption_button.setIcon(qta.icon('fa6s.image'))
        generate_caption_button.setCursor(Qt.PointingHandCursor)
        generate_caption_button.setFixedHeight(36)
        layout.addWidget(generate_caption_button)

        label4 = QLabel('Step 4 Generate Image Hash')
        label4.setAlignment(Qt.AlignLeft)
        layout.addWidget(label4)
        generate_hash_button = QPushButton('Generate Image Hash', self)
        generate_hash_button.setObjectName('generate_hash_button')
        generate_hash_button.setIcon(qta.icon('fa6s.hashtag'))
        generate_hash_button.setCursor(Qt.PointingHandCursor)
        generate_hash_button.setFixedHeight(36)
        layout.addWidget(generate_hash_button)
        layout.addStretch()
    
    def set_current_directory(self, directory_path: str):
        self.current_directory = directory_path
    
    def _refresh_file_pane(self):
        if not self.current_directory:
            return
        
        try:
            sidebar = self.parent()
            if sidebar and hasattr(sidebar, 'content'):
                central = sidebar.content
                if central and hasattr(central, 'manager'):
                    central.manager.load_path(self.current_directory)
        except Exception as e:
            print(f"Error refreshing file pane: {e}")
    
    def _on_scan_directory_clicked(self):
        if not self.current_directory:
            print("No directory selected")
            return
        
        directory_path = Path(self.current_directory)
        if not directory_path.exists() or not directory_path.is_dir():
            print(f"Invalid directory: {self.current_directory}")
            return
        
        try:
            base_path = Path(__file__).parent.parent.parent.parent
            trails_data = scan_directory(directory_path, base_path)
            self.scan_completed.emit(trails_data)
            
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._refresh_file_pane())
            
        except Exception as e:
            print(f"Error during scan: {e}")
