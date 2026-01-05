from pathlib import Path
from PySide6.QtCore import QObject, Signal
from UI.Widgets.CentralWidget.central_widget_file_pane_widget import CentralWidgetFilePaneWidget


class CentralWidgetManager(QObject):
    loading_changed = Signal(bool)
    extensions_found = Signal(list)
    loaded_count_changed = Signal(int, int)
    
    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        self.file_pane = CentralWidgetFilePaneWidget()
        
        self.file_pane.loading_changed.connect(self.loading_changed.emit)
        self.file_pane.extensions_found.connect(self.extensions_found.emit)
        self.file_pane.loaded_count_changed.connect(self.loaded_count_changed.emit)
    
    def get_file_pane(self):
        return self.file_pane
    
    def load_path(self, path_str):
        self.file_pane.load_path(path_str)
    
    def set_view_mode(self, mode):
        self.file_pane.set_view_mode(mode)
    
    def set_sort(self, sort_by):
        self.file_pane.set_sort(sort_by)
    
    def set_grid_width(self, width):
        self.file_pane.set_grid_width(width)

    def search(self, query: str):
        if hasattr(self.file_pane, 'search_and_highlight'):
            self.file_pane.search_and_highlight(query)
