from pathlib import Path

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget, QSizePolicy, QMessageBox, QScrollArea

import qtawesome as qta

from PapikaCore.papika_directory_operations import is_scan_required
from PapikaCore.papika_initiate_directory_scan import scan_directory
from UI.Themes.papika_global_themes import PAPIKA_THEME

class SidebarActionWidget(QWidget):
    scan_completed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.current_directory = None
        self.sizes = PAPIKA_THEME.get_sizes()
        self.spacing = PAPIKA_THEME.get_spacing()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        
        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_widget.setAttribute(Qt.WA_StyledBackground, True)
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(*self.spacing['margins_medium'])
        layout.setSpacing(self.spacing['spacing_medium'])
        
        label = QLabel('Step 1 Scan Directory')
        label.setAlignment(Qt.AlignLeft)
        layout.addWidget(label)
        self.scan_directory_button = QPushButton('Scan Directory', self)
        self.scan_directory_button.setObjectName('scan_directory_button')
        self.scan_directory_button.setIcon(qta.icon('fa6s.folder-open'))
        self.scan_directory_button.setCursor(Qt.PointingHandCursor)
        self.scan_directory_button.setFixedHeight(self.sizes['button_height'])
        self.scan_directory_button.clicked.connect(self._on_scan_directory_clicked)
        layout.addWidget(self.scan_directory_button)
        
        label2 = QLabel('Step 2 Generate Embedding')
        label2.setAlignment(Qt.AlignLeft)
        layout.addWidget(label2)
        generate_embedding_button = QPushButton('Generate Embedding', self)
        generate_embedding_button.setObjectName('generate_embedding_button')
        generate_embedding_button.setIcon(qta.icon('fa6s.wand-magic-sparkles'))
        generate_embedding_button.setCursor(Qt.PointingHandCursor)
        generate_embedding_button.setFixedHeight(self.sizes['button_height'])
        layout.addWidget(generate_embedding_button)

        label3 = QLabel('Step 3 Generate Image Caption')
        label3.setAlignment(Qt.AlignLeft)
        layout.addWidget(label3)
        generate_caption_button = QPushButton('Generate Caption', self)
        generate_caption_button.setObjectName('generate_caption_button')
        generate_caption_button.setIcon(qta.icon('fa6s.image'))
        generate_caption_button.setCursor(Qt.PointingHandCursor)
        generate_caption_button.setFixedHeight(self.sizes['button_height'])
        layout.addWidget(generate_caption_button)

        label4 = QLabel('Step 4 Generate Image Hash')
        label4.setAlignment(Qt.AlignLeft)
        layout.addWidget(label4)
        generate_hash_button = QPushButton('Generate Image Hash', self)
        generate_hash_button.setObjectName('generate_hash_button')
        generate_hash_button.setIcon(qta.icon('fa6s.hashtag'))
        generate_hash_button.setCursor(Qt.PointingHandCursor)
        generate_hash_button.setFixedHeight(self.sizes['button_height'])
        layout.addWidget(generate_hash_button)
        
        self.colors = PAPIKA_THEME.get_colors()
        btn_padding = PAPIKA_THEME.get_spacing()['padding_medium']
        btn_style = (
            f"QPushButton {{ background-color: transparent; border: 1px solid {self.colors['border']}; border-radius: 6px; padding: {btn_padding}; }} "
            f"QPushButton:hover {{ background-color: {self.colors['primary_rgba_light']}; color: {self.colors['primary']}; }}"
        )
        for _btn in (self.scan_directory_button, generate_embedding_button, generate_caption_button, generate_hash_button):
            _btn.setStyleSheet(btn_style)
        
        # set icons with inactive color and install hover event filters to colorize icon on hover
        self._action_button_icon_map = {
            self.scan_directory_button: 'fa6s.folder-open',
            generate_embedding_button: 'fa6s.wand-magic-sparkles',
            generate_caption_button: 'fa6s.image',
            generate_hash_button: 'fa6s.hashtag'
        }
        inactive_color = self.colors.get('icon_inactive', '#9CA3AF')
        for btn, icon_name in self._action_button_icon_map.items():
            btn.setIcon(qta.icon(icon_name, color=inactive_color))
            btn.installEventFilter(self)
        
        layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
    
    def set_current_directory(self, directory_path: str):
        self.current_directory = directory_path
        self._update_scan_button_text()

    def eventFilter(self, obj, event):
        # Handle hover enter/leave for action buttons to colorize icons
        if event.type() == QEvent.Enter and obj in getattr(self, '_action_button_icon_map', {}):
            icon_name = self._action_button_icon_map.get(obj)
            if icon_name:
                obj.setIcon(qta.icon(icon_name, color=self.colors.get('primary')))
        elif event.type() == QEvent.Leave and obj in getattr(self, '_action_button_icon_map', {}):
            icon_name = self._action_button_icon_map.get(obj)
            if icon_name:
                obj.setIcon(qta.icon(icon_name, color=self.colors.get('icon_inactive')))
        return super().eventFilter(obj, event)
    
    def _update_scan_button_text(self):
        if not self.current_directory:
            self.scan_directory_button.setText('Scan Directory')
            return
        
        try:
            base_path = Path(__file__).parent.parent.parent.parent
            if is_scan_required(Path(self.current_directory), base_path):
                self.scan_directory_button.setText('Scan Directory (required)')
            else:
                self.scan_directory_button.setText('Scan Directory')
        except Exception as e:
            print(f"Error updating scan button text: {e}")
            self.scan_directory_button.setText('Scan Directory')
    
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
            QMessageBox.warning(self, "No Directory Selected", "Please select a directory to scan.")
            return
        
        directory_path = Path(self.current_directory)
        if not directory_path.exists() or not directory_path.is_dir():
            QMessageBox.warning(self, "Invalid Directory", f"Invalid directory: {self.current_directory}")
            return
        
        # Disallow scanning of root drives (e.g., 'Z:/') to avoid accidental wide scans
        try:
            if Path(directory_path) == Path(directory_path.anchor):
                QMessageBox.warning(self, "Invalid Selection", "Scanning a root drive is not allowed. Please select a subfolder.")
                return
        except Exception as e:
            print(f"Error checking root drive for scanning: {e}")
        
        try:
            base_path = Path(__file__).parent.parent.parent.parent
            
            existing_images = None
            try:
                sidebar = self.parent()
                if sidebar and hasattr(sidebar, 'content'):
                    central = sidebar.content
                    if central and hasattr(central, 'manager') and hasattr(central.manager, 'file_pane'):
                        file_pane = central.manager.file_pane
                        if hasattr(file_pane, 'images') and file_pane.images:
                            existing_images = file_pane.images
                            print(f"Using existing image list: {len(existing_images)} images")
            except Exception as e:
                print(f"Could not get existing images: {e}")
            
            trails_data = scan_directory(directory_path, base_path, self.window(), existing_images)
            self.scan_completed.emit(trails_data)
            
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self._refresh_file_pane())
            QTimer.singleShot(200, lambda: self._update_scan_button_text())
            
        except Exception as e:
            print(f"Error during scan: {e}")
