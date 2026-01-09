from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QSize, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                               QScrollArea, QGridLayout, QFrame)
from PySide6.QtGui import QPixmap, QIcon, QColor, QBrush
import qtawesome as qta
from UI.Widgets.CentralWidget.central_widget_file_pane_image_preview import ClickableLabel, ImagePreviewOverlay
from UI.Themes.papika_global_themes import PAPIKA_THEME


class ImageLoaderThread(QThread):
    finished = Signal(list)
    
    def __init__(self, path_str):
        super().__init__()
        self.path_str = path_str
    
    def run(self):
        try:
            from PIL import Image
            supported = Image.registered_extensions()
            
            path = Path(self.path_str)
            if not path.exists() or not path.is_dir():
                self.finished.emit([])
                return
            
            images = []
            try:
                for entry in path.iterdir():
                    if entry.is_file():
                        ext = entry.suffix.lower()
                        if ext in supported:
                            images.append(entry)
            except (PermissionError, OSError):
                pass
            
            self.finished.emit(images)
        except Exception as e:
            print(f"Error loading images from {self.path_str}: {e}")
            self.finished.emit([])


class ThumbnailLoaderThread(QThread):
    thumbnail_ready = Signal(str, QPixmap)
    
    def __init__(self, image_path, size):
        super().__init__()
        self.image_path = image_path
        self.size = size
    
    def run(self):
        try:
            pixmap = QPixmap(str(self.image_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.thumbnail_ready.emit(str(self.image_path), scaled)
        except Exception as e:
            print(f"Error loading thumbnail {self.image_path}: {e}")


class CentralWidgetFilePaneWidget(QWidget):
    loading_changed = Signal(bool)
    extensions_found = Signal(list)
    loaded_count_changed = Signal(int, int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = None
        self.current_view = 'grid'
        self.current_sort = 'Name'
        self.grid_width = 6
        self.images = []
        self.loader_thread = None
        self.thumbnail_cache = {}
        self.visible_items = set()
        self.thumbnail_queue = []
        self.active_thumbnail_threads = []
        self.cached_grid_size = 0
        self.loaded_count = 0
        self.chunk_size = 200
        self.is_loading_chunk = False
        self.current_search_query = ''
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._on_resize_complete)
        self.spacing = PAPIKA_THEME.get_spacing()
        self.colors = PAPIKA_THEME.get_colors()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(*self.spacing['margins_none'])
        self.layout.setSpacing(0)
        
        self.list_view = QListWidget()
        self.list_view.setIconSize(QSize(48, 48))
        self.list_view.setVisible(True)
        self.list_view.verticalScrollBar().valueChanged.connect(self._on_list_scroll)
        self.layout.addWidget(self.list_view)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_grid_scroll)
        self.grid_container = QWidget()
        self._grid_gap = self.spacing['spacing_small'] - 4
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(self._grid_gap)
        self.grid_layout.setHorizontalSpacing(self._grid_gap)
        self.grid_layout.setVerticalSpacing(self._grid_gap)
        self.grid_layout.setContentsMargins(*[self._grid_gap]*4)
        self._grid_border_reserve = self.spacing['spacing_small'] - 4
        self.scroll_area.setWidget(self.grid_container)
        self.scroll_area.setVisible(False)
        self.layout.addWidget(self.scroll_area)
        
        self.table_view = QTableWidget()
        self.table_view.setColumnCount(3)
        self.table_view.setHorizontalHeaderLabels(['Name', 'Size', 'Modified'])
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_view.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_view.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_view.setVisible(False)
        self.layout.addWidget(self.table_view)
        
        self.load_timer = QTimer()
        self.load_timer.setSingleShot(True)
        self.load_timer.timeout.connect(self._load_next_thumbnail)
        self.preview_overlay = ImagePreviewOverlay(self)
        self.set_view_mode('grid')
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.current_view == 'grid' and self.images:
            self.resize_timer.start(150)
    
    def _on_resize_complete(self):
        if self.current_view == 'grid' and self.images:
            available_width = self.scroll_area.viewport().width()
            spacing = self._grid_gap
            total_spacing = spacing * (self.grid_width - 1) + (2 * self._grid_gap)
            item_size = max(50, (available_width - total_spacing) // self.grid_width)
            
            if abs(item_size - self.cached_grid_size) > 6:
                self.cached_grid_size = item_size
                self.thumbnail_cache.clear()
                self.loading_changed.emit(True)
                self._populate_grid_view()
                QTimer.singleShot(100, self._load_visible_grid_items)
                self.loading_changed.emit(False)
    
    def load_path(self, path_str):
        if not path_str or path_str == "network://":
            self._clear_views()
            self.loading_changed.emit(False)
            self.loaded_count_changed.emit(0, 0)
            self.extensions_found.emit([])
            return
        
        self.current_path = path_str
        self.loading_changed.emit(True)
        
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.finished.disconnect()
            self.loader_thread.quit()
            self.loader_thread.wait()
        
        self.loader_thread = ImageLoaderThread(path_str)
        self.loader_thread.finished.connect(self._populate_images)
        self.loader_thread.start()
    
    def _populate_images(self, images):
        self.loading_changed.emit(False)
        self.images = images
        self._sort_images()
        
        extensions = set()
        for img in images:
            extensions.add(img.suffix.lower())
        self.extensions_found.emit(sorted(extensions))
        
        if self.current_view == 'list':
            self._populate_list_view()
        elif self.current_view == 'grid':
            self._populate_grid_view()
        elif self.current_view == 'details':
            self._populate_details_view()
    
    def _populate_list_view(self):
        self.list_view.clear()
        self.visible_items.clear()
        self.thumbnail_queue.clear()
        self.loaded_count = 0
        self.is_loading_chunk = False
        
        self._load_list_chunk()
    
    def _load_list_chunk(self):
        if self.is_loading_chunk or self.loaded_count >= len(self.images):
            return
        
        self.is_loading_chunk = True
        placeholder_icon = qta.icon('fa6s.image', color=self.colors['primary'])
        
        end_index = min(self.loaded_count + self.chunk_size, len(self.images))
        
        for idx in range(self.loaded_count, end_index):
            img_path = self.images[idx]
            item = QListWidgetItem()
            item.setText(img_path.name)
            item.setData(Qt.UserRole, str(img_path))
            
            img_path_str = str(img_path)
            if img_path_str in self.thumbnail_cache:
                item.setIcon(QIcon(self.thumbnail_cache[img_path_str]))
                self.visible_items.add(img_path_str)
            else:
                item.setIcon(placeholder_icon)
            
            self.list_view.addItem(item)
        
        self.loaded_count = end_index
        self.is_loading_chunk = False
        
        if self.loaded_count < len(self.images):
            status_text = f"Loaded {self.loaded_count} of {len(self.images)} images"
            print(status_text)
        
        self.loaded_count_changed.emit(self.loaded_count, len(self.images))
        self._load_visible_list_items()
        
        if self.current_search_query:
            QTimer.singleShot(10, lambda: self.search_and_highlight(self.current_search_query))
    
    def _on_list_scroll(self):
        scrollbar = self.list_view.verticalScrollBar()
        if scrollbar.value() > scrollbar.maximum() - 100:
            if self.loaded_count < len(self.images):
                self._load_list_chunk()
        self._load_visible_list_items()
    
    def _load_visible_list_items(self):
        first_visible = self.list_view.indexAt(self.list_view.rect().topLeft()).row()
        last_visible = self.list_view.indexAt(self.list_view.rect().bottomLeft()).row()
        
        if first_visible == -1:
            first_visible = 0
        if last_visible == -1:
            last_visible = self.list_view.count() - 1
        
        for i in range(max(0, first_visible - 5), min(self.list_view.count(), last_visible + 6)):
            item = self.list_view.item(i)
            if item:
                img_path = item.data(Qt.UserRole)
                if img_path and img_path not in self.visible_items:
                    self.visible_items.add(img_path)
                    if img_path not in self.thumbnail_cache:
                        self.thumbnail_queue.append((img_path, 48))
        
        if self.thumbnail_queue:
            if not self.load_timer.isActive():
                self.loading_changed.emit(True)
                self.load_timer.start(10)
    
    def _populate_grid_view(self):
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.visible_items.clear()
        self.thumbnail_queue.clear()
        self.loaded_count = 0
        self.is_loading_chunk = False
        
        available_width = self.scroll_area.viewport().width() - 20
        spacing = 5
        total_spacing = spacing * (self.grid_width - 1)
        item_size = max(50, (available_width - total_spacing) // self.grid_width)
        self.cached_grid_size = item_size
        
        self._load_grid_chunk()
    
    def _load_grid_chunk(self):
        if self.is_loading_chunk or self.loaded_count >= len(self.images):
            return
        
        self.is_loading_chunk = True
        
        available_width = self.scroll_area.viewport().width()
        spacing = self._grid_gap
        total_spacing = spacing * (self.grid_width - 1) + (2 * self._grid_gap)
        item_size = max(50, (available_width - total_spacing) // self.grid_width)
        content_size = max(16, item_size - (2 * self._grid_border_reserve))
        
        end_index = min(self.loaded_count + self.chunk_size, len(self.images))
        
        for idx in range(self.loaded_count, end_index):
            img_path = self.images[idx]
            row = idx // self.grid_width
            col = idx % self.grid_width
            
            img_label = ClickableLabel()
            img_label.setFixedSize(item_size, item_size)
            img_label.setAlignment(Qt.AlignCenter)
            img_path_str = str(img_path)
            img_label.setProperty('image_path', img_path_str)
            img_label.setProperty('target_size', content_size)
            
            cache_key = f"{img_path_str}_{content_size}"
            if cache_key in self.thumbnail_cache:
                img_label.setPixmap(self.thumbnail_cache[cache_key])
                self.visible_items.add(img_path_str)
            else:
                icon_size = max(16, min(64, content_size - 8))
                placeholder_icon = qta.icon('fa6s.image', color=self.colors['primary'])
                placeholder_pixmap = placeholder_icon.pixmap(QSize(icon_size, icon_size))
                img_label.setPixmap(placeholder_pixmap)

            img_label.double_clicked.connect(self._on_grid_item_double_clicked)
            self._apply_grid_item_baseline(img_label)
            self.grid_layout.addWidget(img_label, row, col)
        
        self.loaded_count = end_index
        self.is_loading_chunk = False
        
        if self.loaded_count < len(self.images):
            status_text = f"Loaded {self.loaded_count} of {len(self.images)} images"
            print(status_text)
        
        self.loaded_count_changed.emit(self.loaded_count, len(self.images))
        QTimer.singleShot(30, self._load_visible_grid_items)
        
        if self.current_search_query:
            QTimer.singleShot(40, lambda: self.search_and_highlight(self.current_search_query))
    
    def _on_grid_scroll(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        if scrollbar.value() > scrollbar.maximum() - 200:
            if self.loaded_count < len(self.images):
                self._load_grid_chunk()
        self._load_visible_grid_items()

    def _on_grid_item_double_clicked(self, path_str: str):
        if path_str and self.preview_overlay:
            self.preview_overlay.show_image(path_str)
    
    def _load_visible_grid_items(self):
        viewport_rect = self.scroll_area.viewport().rect()
        
        for i in range(self.grid_layout.count()):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget_pos = widget.mapTo(self.scroll_area.viewport(), widget.rect().topLeft())
                widget_rect = widget.rect()
                widget_rect.moveTo(widget_pos)
                
                if viewport_rect.intersects(widget_rect):
                    img_path = widget.property('image_path')
                    target_size = widget.property('target_size')
                    if img_path and img_path not in self.visible_items:
                        self.visible_items.add(img_path)
                        cache_key = f"{img_path}_{target_size}"
                        if cache_key not in self.thumbnail_cache:
                            self.thumbnail_queue.append((img_path, target_size))
        
        if self.thumbnail_queue:
            if not self.load_timer.isActive():
                self.loading_changed.emit(True)
                self.load_timer.start(10)

    def _grid_item_baseline(self):
        border_color = self.colors['primary']
        return f"QLabel {{ border: 0px solid transparent; padding: 1px; border-radius: 4px; }} QLabel:hover {{ border: 2px solid {border_color}; padding: 1px; border-radius: 4px; }}"

    def _apply_grid_item_baseline(self, widget):
        widget.setAttribute(Qt.WA_Hover, True)
        widget.setContentsMargins(*self.spacing['margins_custom_1'])
        widget.setStyleSheet(self._grid_item_baseline())

    def _apply_grid_item_highlight(self, widget):
        widget.setAttribute(Qt.WA_Hover, True)
        widget.setContentsMargins(*self.spacing['margins_custom_1'])
        border_color = self.colors['primary']
        widget.setStyleSheet(f"QLabel {{ border: 2px solid {border_color}; padding: 1px; border-radius: 4px; }} QLabel:hover {{ border: 2px solid {border_color}; padding: 1px; border-radius: 4px; }}")    
    def _populate_details_view(self):
        self.table_view.setRowCount(len(self.images))
        for idx, img_path in enumerate(self.images):
            name_item = QTableWidgetItem(img_path.name)
            self.table_view.setItem(idx, 0, name_item)
            
            try:
                size = img_path.stat().st_size
                size_str = self._format_size(size)
                size_item = QTableWidgetItem(size_str)
                self.table_view.setItem(idx, 1, size_item)
            except Exception:
                self.table_view.setItem(idx, 1, QTableWidgetItem(''))
            
            try:
                mtime = img_path.stat().st_mtime
                from datetime import datetime
                dt = datetime.fromtimestamp(mtime)
                date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                date_item = QTableWidgetItem(date_str)
                self.table_view.setItem(idx, 2, date_item)
            except Exception:
                self.table_view.setItem(idx, 2, QTableWidgetItem(''))
    
    def set_view_mode(self, mode):
        self.current_view = mode
        
        self.list_view.setVisible(mode == 'list')
        self.scroll_area.setVisible(mode == 'grid')
        self.table_view.setVisible(mode == 'details')
        
        if self.images:
            if mode == 'list':
                self._populate_list_view()
                if self.current_search_query:
                    QTimer.singleShot(20, lambda q=self.current_search_query: self.search_and_highlight(q))
            elif mode == 'grid':
                self._populate_grid_view()
                if self.current_search_query:
                    QTimer.singleShot(40, lambda q=self.current_search_query: self.search_and_highlight(q))
            elif mode == 'details':
                self._populate_details_view()
                if self.current_search_query:
                    QTimer.singleShot(20, lambda q=self.current_search_query: self.search_and_highlight(q))
    
    def set_sort(self, sort_by):
        self.current_sort = sort_by
        self._sort_images()
        
        if self.images:
            if self.current_view == 'list':
                self._populate_list_view()
            elif self.current_view == 'grid':
                self._populate_grid_view()
            elif self.current_view == 'details':
                self._populate_details_view()
    
    def set_grid_width(self, width):
        self.grid_width = width
        if self.current_view == 'grid' and self.images:
            self._populate_grid_view()
            QTimer.singleShot(100, self._load_visible_grid_items)
    
    def _load_next_thumbnail(self):
        if not self.thumbnail_queue:
            self.loading_changed.emit(False)
            return
        
        img_path, size = self.thumbnail_queue.pop(0)
        
        thread = ThumbnailLoaderThread(img_path, size)
        thread.thumbnail_ready.connect(self._on_thumbnail_ready)
        thread.finished.connect(lambda: self._cleanup_thumbnail_thread(thread))
        self.active_thumbnail_threads.append(thread)
        thread.start()
        
        if self.thumbnail_queue:
            self.load_timer.start(10)
        else:
            self.loading_changed.emit(False)
    
    def _on_thumbnail_ready(self, img_path, pixmap):
        if self.current_view == 'list':
            self.thumbnail_cache[img_path] = pixmap
            for i in range(self.list_view.count()):
                item = self.list_view.item(i)
                if item and item.data(Qt.UserRole) == img_path:
                    item.setIcon(QIcon(pixmap))
                    break
        elif self.current_view == 'grid':
            for i in range(self.grid_layout.count()):
                widget = self.grid_layout.itemAt(i).widget()
                if widget and widget.property('image_path') == img_path:
                    target_size = widget.property('target_size')
                    cache_key = f"{img_path}_{target_size}"
                    self.thumbnail_cache[cache_key] = pixmap
                    widget.setPixmap(pixmap)
                    break
    
    def _cleanup_thumbnail_thread(self, thread):
        if thread in self.active_thumbnail_threads:
            self.active_thumbnail_threads.remove(thread)
    
    def _sort_images(self):
        if not self.images:
            return
        
        sort_by = self.current_sort
        
        if sort_by == 'Name':
            self.images.sort(key=lambda p: p.name.lower())
        elif sort_by == 'Size':
            self.images.sort(key=lambda p: p.stat().st_size if p.exists() else 0, reverse=True)
        elif sort_by == 'Date':
            self.images.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
        else:
            ext = sort_by.lower()
            self.images.sort(key=lambda p: (p.suffix.lower() != ext, p.name.lower()))
    
    def _clear_views(self):
        self.list_view.clear()
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.table_view.setRowCount(0)
        self.images = []
    
    def _format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def search_and_highlight(self, query: str):
        q = (query or '').strip().lower()
        self.current_search_query = q
        orange = (247, 161, 40)
        bg_alpha = 60
        highlight_color = QColor(orange[0], orange[1], orange[2], bg_alpha)
        clear_brush = QBrush(QColor(0, 0, 0, 0))

        if self.current_view == 'list':
            if q:
                first_match_index = -1
                for idx, img_path in enumerate(self.images):
                    if q in img_path.name.lower():
                        first_match_index = idx
                        break
                
                if first_match_index >= 0:
                    while self.loaded_count <= first_match_index and self.loaded_count < len(self.images):
                        self._load_list_chunk()
                    
                    for i in range(self.list_view.count()):
                        item = self.list_view.item(i)
                        if not item:
                            continue
                        name = item.text().lower()
                        if q in name:
                            item.setBackground(QBrush(highlight_color))
                        else:
                            item.setBackground(clear_brush)
                    
                    for i in range(self.list_view.count()):
                        item = self.list_view.item(i)
                        if item and q in item.text().lower():
                            self.list_view.scrollToItem(item)
                            break
            else:
                for i in range(self.list_view.count()):
                    item = self.list_view.item(i)
                    if item:
                        item.setBackground(clear_brush)
            return

        if self.current_view == 'grid':
            if q:
                first_match_index = -1
                for idx, img_path in enumerate(self.images):
                    if q in img_path.name.lower():
                        first_match_index = idx
                        break
                
                if first_match_index >= 0:
                    while self.loaded_count <= first_match_index and self.loaded_count < len(self.images):
                        self._load_grid_chunk()
                    
                    first_found = None
                    for i in range(self.grid_layout.count()):
                        widget = self.grid_layout.itemAt(i).widget()
                        if not widget:
                            continue
                        img_path = widget.property('image_path')
                        name = Path(img_path).name.lower() if img_path else ''
                        if q in name:
                            self._apply_grid_item_highlight(widget)
                            if first_found is None:
                                first_found = widget
                        else:
                            self._apply_grid_item_baseline(widget)
                    
                    if first_found is not None:
                        self.scroll_area.ensureWidgetVisible(first_found)
            else:
                for i in range(self.grid_layout.count()):
                    widget = self.grid_layout.itemAt(i).widget()
                    if widget:
                        self._apply_grid_item_baseline(widget)
            return

        if self.current_view == 'details':
            rows = self.table_view.rowCount()
            for r in range(rows):
                cell = self.table_view.item(r, 0)
                if not cell:
                    continue
                name = cell.text().lower()
                if q and q in name:
                    for c in range(self.table_view.columnCount()):
                        it = self.table_view.item(r, c)
                        if it:
                            it.setBackground(QBrush(highlight_color))
                else:
                    for c in range(self.table_view.columnCount()):
                        it = self.table_view.item(r, c)
                        if it:
                            it.setBackground(clear_brush)
            if q:
                for r in range(rows):
                    cell = self.table_view.item(r, 0)
                    if cell and q in cell.text().lower():
                        self.table_view.scrollToItem(cell, QTableWidget.PositionAtTop)
                        break
