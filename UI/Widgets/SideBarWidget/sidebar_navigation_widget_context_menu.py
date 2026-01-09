from pathlib import Path

from PySide6.QtCore import Signal, QObject
from PySide6.QtWidgets import QMenu, QMessageBox

import qtawesome as qta

from Configs.configs_file_manager import load_config
from PapikaCore.papika_directory_operations import is_scan_required


class SidebarNavigationContextMenu(QObject):
    remove_footprints_requested = Signal(str)
    scan_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def create_menu(self, path: str, parent_widget):
        menu = QMenu(parent_widget)
        
        if path and path != "network://":
            base_path = Path(__file__).parent.parent.parent.parent
            scan_text = "Scan Directory"
            if is_scan_required(Path(path), base_path):
                scan_text = "Scan Directory (required)"
            
            scan_action = menu.addAction(scan_text)
            scan_action.setIcon(qta.icon('fa6s.folder-open'))
            scan_action.triggered.connect(lambda: self.scan_requested.emit(path))
            
            remove_action = menu.addAction("Remove Papika's Footprints")
            remove_action.setIcon(qta.icon('fa6s.paw'))
            remove_action.triggered.connect(lambda: self._on_remove_footprints(path, parent_widget))
        
        return menu
    
    def _on_remove_footprints(self, path: str, parent_widget):
        try:
            base_path = Path(__file__).parent.parent.parent.parent
            configs = load_config(base_path)
            
            directory_path = Path(path)
            footprints_folder = directory_path / configs['database']['directory']
            
            if not footprints_folder.exists():
                QMessageBox.warning(
                    parent_widget,
                    "Not Found",
                    f"Papika has not scanned folder '{directory_path.name}' yet",
                    QMessageBox.Ok
                )
                return
            
            reply = QMessageBox.question(
                parent_widget,
                "Remove Papika's Footprints",
                f"Are you sure you want to remove Papika's footprints from this directory?\n\n{path}\n\nThis will delete the database and all processed data.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.remove_footprints_requested.emit(path)
        except Exception as e:
            print(f"Error checking footprints folder: {e}")
