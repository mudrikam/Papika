from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QSize, QTimer, QRect
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                               QLabel, QTableWidget, QTableWidgetItem, QHeaderView,
                               QScrollArea, QGridLayout, QFrame, QAbstractItemView)
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
    thumbnail_ready = Signal(str, int, QPixmap)
    
    def __init__(self, image_path, size):
        super().__init__()
        self.image_path = image_path
        self.size = size
    
    def run(self):
        try:
            pixmap = QPixmap(str(self.image_path))
            if not pixmap.isNull():
                scaled = pixmap.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.thumbnail_ready.emit(str(self.image_path), self.size, scaled)
        except Exception as e:
            print(f"Error loading thumbnail {self.image_path}: {e}")


class CentralWidgetFilePaneWidget(QWidget):
    loading_changed = Signal(bool)
    extensions_found = Signal(list)
    loaded_count_changed = Signal(int, int)
    
    BUFFER_ROWS_AHEAD = 5
    BUFFER_ROWS_BEHIND = 2
    MAX_CONCURRENT_THUMBNAILS = 6
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = None
        self.current_view = 'grid'
        self.current_sort = 'Name'
        self.grid_width = 6
        self.images = []
        self.loader_thread = None
        self.thumbnail_cache = {}
        self.thumbnail_queue = []
        self.active_thumbnail_threads = []
        self.cached_grid_size = 0
        self.current_search_query = ''
        
        self.visible_start_idx = 0
        self.visible_end_idx = 0
        self.grid_widgets = {}
        self.widget_pool = []
        self.item_height = 0
        
        self.last_scroll_y = 0
        self.scroll_direction = 1
        
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._on_resize_complete)
        
        self.scroll_timer = QTimer()
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self._on_scroll_settle)
        
        self.preload_timer = QTimer()
        self.preload_timer.setSingleShot(True)
        self.preload_timer.timeout.connect(self._preload_ahead)
        
        self.middle_mouse_scrolling = False
        self.middle_click_pos = None
        self.middle_scroll_speed_x = 0
        self.middle_scroll_speed_y = 0
        self.middle_scroll_indicator = None
        
        self.auto_scroll_timer = QTimer()
        self.auto_scroll_timer.timeout.connect(self._apply_auto_scroll)
        
        self.spacing = PAPIKA_THEME.get_spacing()
        self.colors = PAPIKA_THEME.get_colors()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(*self.spacing['margins_none'])
        self.layout.setSpacing(0)
        
        self.list_view = QListWidget()
        self.list_view.setIconSize(QSize(48, 48))
        self.list_view.setVisible(True)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setLayoutMode(QListWidget.Batched)
        self.list_view.setBatchSize(50)
        self.list_view.verticalScrollBar().valueChanged.connect(self._on_list_scroll)
        self.layout.addWidget(self.list_view)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_grid_scroll)
        self.scroll_area.viewport().installEventFilter(self)
        self.grid_container = QWidget()
        self._grid_gap = self.spacing['spacing_small'] - 4
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
    
    def eventFilter(self, obj, event):
        if obj == self.scroll_area.viewport():
            from PySide6.QtCore import QEvent
            from PySide6.QtGui import QMouseEvent
            
            if event.type() == QEvent.Resize:
                if self.current_view == 'grid' and self.images:
                    self.resize_timer.start(100)
            elif event.type() == QEvent.MouseButtonPress:
                mouse_event = event
                if mouse_event.button() == Qt.MiddleButton:
                    self._start_middle_mouse_scroll(mouse_event.pos())
                    return True
            elif event.type() == QEvent.MouseMove:
                if self.middle_mouse_scrolling:
                    self._update_middle_mouse_scroll(event.pos())
                    return True
            elif event.type() == QEvent.MouseButtonRelease:
                if self.middle_mouse_scrolling:
                    self._stop_middle_mouse_scroll()
                    return True
            elif event.type() == QEvent.Leave:
                if self.middle_mouse_scrolling:
                    self._stop_middle_mouse_scroll()
        return super().eventFilter(obj, event)
    
    def _on_resize_complete(self):
        if self.current_view == 'grid' and self.images:
            available_width = self.scroll_area.viewport().width()
            spacing = self._grid_gap
            total_spacing = spacing * (self.grid_width - 1) + (2 * self._grid_gap)
            item_size = max(50, (available_width - total_spacing) // self.grid_width)
            
            if abs(item_size - self.cached_grid_size) > 6:
                self.cached_grid_size = item_size
                self.item_height = item_size + self._grid_gap
                self._rebuild_grid_virtual()
    
    def _start_middle_mouse_scroll(self, pos):
        self.middle_mouse_scrolling = True
        self.middle_click_pos = pos
        self.middle_scroll_speed_x = 0
        self.middle_scroll_speed_y = 0
        
        self.scroll_area.viewport().setCursor(Qt.SizeAllCursor)
        
        if not self.middle_scroll_indicator:
            from PySide6.QtWidgets import QLabel
            from PySide6.QtGui import QPainter, QPen, QBrush
            self.middle_scroll_indicator = QLabel(self.scroll_area.viewport())
            self.middle_scroll_indicator.setFixedSize(40, 40)
            self.middle_scroll_indicator.setStyleSheet(
                "QLabel { background-color: rgba(100, 100, 100, 180); border-radius: 20px; border: 2px solid rgba(255, 255, 255, 200); }"
            )
        
        self.middle_scroll_indicator.move(pos.x() - 20, pos.y() - 20)
        self.middle_scroll_indicator.show()
        self.middle_scroll_indicator.raise_()
        
        self.auto_scroll_timer.start(16)
    
    def _update_middle_mouse_scroll(self, pos):
        if not self.middle_mouse_scrolling or not self.middle_click_pos:
            return
        
        delta_x = pos.x() - self.middle_click_pos.x()
        delta_y = pos.y() - self.middle_click_pos.y()
        
        speed_factor = 0.15
        max_speed = 50
        
        self.middle_scroll_speed_x = max(-max_speed, min(max_speed, delta_x * speed_factor))
        self.middle_scroll_speed_y = max(-max_speed, min(max_speed, delta_y * speed_factor))
    
    def _apply_auto_scroll(self):
        if not self.middle_mouse_scrolling:
            self.auto_scroll_timer.stop()
            return
        
        if abs(self.middle_scroll_speed_y) > 0.5:
            current_y = self.scroll_area.verticalScrollBar().value()
            new_y = int(current_y + self.middle_scroll_speed_y)
            self.scroll_area.verticalScrollBar().setValue(new_y)
        
        if abs(self.middle_scroll_speed_x) > 0.5:
            current_x = self.scroll_area.horizontalScrollBar().value()
            new_x = int(current_x + self.middle_scroll_speed_x)
            self.scroll_area.horizontalScrollBar().setValue(new_x)
    
    def _stop_middle_mouse_scroll(self):
        if not self.middle_mouse_scrolling:
            return
        
        self.middle_mouse_scrolling = False
        self.middle_click_pos = None
        self.middle_scroll_speed_x = 0
        self.middle_scroll_speed_y = 0
        
        self.auto_scroll_timer.stop()
        
        if self.middle_scroll_indicator:
            self.middle_scroll_indicator.hide()
            self.middle_scroll_indicator.deleteLater()
            self.middle_scroll_indicator = None
        
        self.scroll_area.viewport().setCursor(Qt.ArrowCursor)
    
    def _on_scroll_settle(self):
        if self.current_view == 'list':
            self._load_visible_list_thumbnails()
    
    def load_path(self, path_str):
        if not path_str or path_str == "network://":
            self._clear_views()
            self.loading_changed.emit(False)
            self.loaded_count_changed.emit(0, 0)
            self.extensions_found.emit([])
            return
        
        self.current_path = path_str
        self.loading_changed.emit(True)
        
        self._cancel_all_thumbnail_threads()
        
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.finished.disconnect()
            self.loader_thread.quit()
            self.loader_thread.wait()
        
        self.loader_thread = ImageLoaderThread(path_str)
        self.loader_thread.finished.connect(self._populate_images)
        self.loader_thread.start()
    
    def _cancel_all_thumbnail_threads(self):
        self.thumbnail_queue.clear()
        for thread in self.active_thumbnail_threads:
            if thread.isRunning():
                thread.quit()
        self.active_thumbnail_threads.clear()
    
    def _populate_images(self, images):
        self.loading_changed.emit(False)
        self.images = images
        self._sort_images()
        
        extensions = set()
        for img in images:
            extensions.add(img.suffix.lower())
        self.extensions_found.emit(sorted(extensions))
        
        self.loaded_count_changed.emit(len(images), len(images))
        
        if self.current_view == 'list':
            self._populate_list_view()
        elif self.current_view == 'grid':
            self._populate_grid_view()
        elif self.current_view == 'details':
            self._populate_details_view()
    
    def _populate_list_view(self):
        self.list_view.clear()
        self.thumbnail_queue.clear()
        
        placeholder_icon = qta.icon('fa6s.image', color=self.colors['primary'])
        
        self.list_view.setUpdatesEnabled(False)
        for img_path in self.images:
            item = QListWidgetItem()
            item.setText(img_path.name)
            item.setData(Qt.UserRole, str(img_path))
            
            img_path_str = str(img_path)
            cache_key = f"{img_path_str}_48"
            if cache_key in self.thumbnail_cache:
                item.setIcon(QIcon(self.thumbnail_cache[cache_key]))
            else:
                item.setIcon(placeholder_icon)
            
            self.list_view.addItem(item)
        self.list_view.setUpdatesEnabled(True)
        
        QTimer.singleShot(50, self._load_visible_list_thumbnails)
        
        if self.current_search_query:
            QTimer.singleShot(60, lambda: self.search_and_highlight(self.current_search_query))
    
    def _on_list_scroll(self):
        self.scroll_timer.start(50)
    
    def _load_visible_list_thumbnails(self):
        first_visible = self.list_view.indexAt(self.list_view.rect().topLeft()).row()
        last_visible = self.list_view.indexAt(self.list_view.rect().bottomLeft()).row()
        
        if first_visible == -1:
            first_visible = 0
        if last_visible == -1:
            last_visible = min(20, self.list_view.count() - 1)
        
        buffer_size = 10
        start_idx = max(0, first_visible - buffer_size)
        end_idx = min(self.list_view.count(), last_visible + buffer_size + 1)
        
        for i in range(start_idx, end_idx):
            item = self.list_view.item(i)
            if item:
                img_path = item.data(Qt.UserRole)
                if img_path:
                    cache_key = f"{img_path}_48"
                    if cache_key not in self.thumbnail_cache and (img_path, 48) not in self.thumbnail_queue:
                        self.thumbnail_queue.append((img_path, 48))
        
        if self.thumbnail_queue and not self.load_timer.isActive():
            self.loading_changed.emit(True)
            self.load_timer.start(5)
    
    def _populate_grid_view(self):
        self._clear_grid_widgets()
        self.thumbnail_queue.clear()
        self.visible_start_idx = 0
        self.visible_end_idx = 0
        
        if not self.images:
            return
        
        available_width = self.scroll_area.viewport().width()
        spacing = self._grid_gap
        total_spacing = spacing * (self.grid_width + 1)
        item_size = max(50, (available_width - total_spacing) // self.grid_width)
        self.cached_grid_size = item_size
        self.item_height = item_size + spacing
        
        total_rows = (len(self.images) + self.grid_width - 1) // self.grid_width
        total_height = total_rows * self.item_height + spacing
        container_width = self.grid_width * item_size + (self.grid_width + 1) * spacing
        
        self.grid_container.setFixedSize(max(container_width, available_width), total_height)
        
        QTimer.singleShot(10, self._update_visible_grid_range)
        
        if self.current_search_query:
            QTimer.singleShot(100, lambda: self.search_and_highlight(self.current_search_query))
    
    def _rebuild_grid_virtual(self):
        if not self.images:
            return
        
        self._clear_grid_widgets()
        self.thumbnail_queue.clear()
        
        available_width = self.scroll_area.viewport().width()
        spacing = self._grid_gap
        total_spacing = spacing * (self.grid_width + 1)
        item_size = max(50, (available_width - total_spacing) // self.grid_width)
        self.cached_grid_size = item_size
        self.item_height = item_size + spacing
        
        total_rows = (len(self.images) + self.grid_width - 1) // self.grid_width
        total_height = total_rows * self.item_height + spacing
        container_width = self.grid_width * item_size + (self.grid_width + 1) * spacing
        
        self.grid_container.setFixedSize(max(container_width, available_width), total_height)
        
        self.visible_start_idx = 0
        self.visible_end_idx = 0
        
        QTimer.singleShot(10, self._update_visible_grid_range)
    
    def _clear_grid_widgets(self):
        for idx, widget in list(self.grid_widgets.items()):
            widget.setParent(None)
            widget.deleteLater()
        self.grid_widgets.clear()
        
        for widget in self.widget_pool:
            widget.setParent(None)
            widget.deleteLater()
        self.widget_pool.clear()
    
    def _update_visible_grid_range(self):
        if not self.images or self.item_height <= 0:
            return
        
        scroll_y = self.scroll_area.verticalScrollBar().value()
        viewport_height = self.scroll_area.viewport().height()
        
        if self.scroll_direction > 0:
            buffer_before = self.BUFFER_ROWS_BEHIND
            buffer_after = self.BUFFER_ROWS_AHEAD
        else:
            buffer_before = self.BUFFER_ROWS_AHEAD
            buffer_after = self.BUFFER_ROWS_BEHIND
        
        first_visible_row = max(0, scroll_y // self.item_height - buffer_before)
        last_visible_row = (scroll_y + viewport_height) // self.item_height + buffer_after + 1
        
        total_rows = (len(self.images) + self.grid_width - 1) // self.grid_width
        last_visible_row = min(last_visible_row, total_rows - 1)
        first_visible_row = max(0, first_visible_row)
        
        new_start = first_visible_row * self.grid_width
        new_end = min((last_visible_row + 1) * self.grid_width, len(self.images))
        
        visible_count = new_end - new_start
        self.loaded_count_changed.emit(visible_count, len(self.images))
        
        if new_start == self.visible_start_idx and new_end == self.visible_end_idx:
            return
        
        current_indices = set(self.grid_widgets.keys())
        needed_indices = set(range(new_start, new_end))
        
        indices_to_remove = current_indices - needed_indices
        for idx in indices_to_remove:
            widget = self.grid_widgets.pop(idx)
            widget.hide()
            self.widget_pool.append(widget)
        
        indices_to_add = needed_indices - current_indices
        self._create_grid_items(indices_to_add)
        
        self.visible_start_idx = new_start
        self.visible_end_idx = new_end
        
        self._queue_visible_thumbnails()
    
    def _preload_ahead(self):
        if not self.images or self.item_height <= 0:
            return
        
        scroll_y = self.scroll_area.verticalScrollBar().value()
        viewport_height = self.scroll_area.viewport().height()
        total_rows = (len(self.images) + self.grid_width - 1) // self.grid_width
        
        if self.scroll_direction > 0:
            preload_start_row = (scroll_y + viewport_height) // self.item_height + self.BUFFER_ROWS_AHEAD
            preload_end_row = min(preload_start_row + 3, total_rows - 1)
        else:
            preload_end_row = scroll_y // self.item_height - self.BUFFER_ROWS_AHEAD
            preload_start_row = max(preload_end_row - 3, 0)
        
        if preload_start_row < 0 or preload_end_row < 0:
            return
        
        preload_start = max(0, preload_start_row * self.grid_width)
        preload_end = min((preload_end_row + 1) * self.grid_width, len(self.images))
        
        content_size = max(16, self.cached_grid_size - (2 * self._grid_border_reserve))
        
        for idx in range(preload_start, preload_end):
            if idx >= len(self.images):
                break
            img_path_str = str(self.images[idx])
            cache_key = f"{img_path_str}_{content_size}"
            if cache_key not in self.thumbnail_cache and (img_path_str, content_size) not in self.thumbnail_queue:
                self.thumbnail_queue.insert(0, (img_path_str, content_size))
        
        if self.thumbnail_queue and not self.load_timer.isActive():
            self.loading_changed.emit(True)
            self.load_timer.start(5)
    
    def _create_grid_items(self, indices):
        if not indices:
            return
        
        spacing = self._grid_gap
        item_size = self.cached_grid_size
        content_size = max(16, item_size - (2 * self._grid_border_reserve))
        
        placeholder_icon = qta.icon('fa6s.image', color=self.colors['primary'])
        icon_size = max(16, min(64, content_size - 8))
        placeholder_pixmap = placeholder_icon.pixmap(QSize(icon_size, icon_size))
        
        for idx in indices:
            if idx >= len(self.images):
                continue
            
            img_path = self.images[idx]
            row = idx // self.grid_width
            col = idx % self.grid_width
            
            x = spacing + col * (item_size + spacing)
            y = spacing + row * (item_size + spacing)
            
            if self.widget_pool:
                img_label = self.widget_pool.pop()
                img_label.setParent(self.grid_container)
            else:
                img_label = ClickableLabel(self.grid_container)
                img_label.double_clicked.connect(self._on_grid_item_double_clicked)
            
            img_label.setFixedSize(item_size, item_size)
            img_label.setGeometry(x, y, item_size, item_size)
            img_label.setAlignment(Qt.AlignCenter)
            img_path_str = str(img_path)
            img_label.setProperty('image_path', img_path_str)
            img_label.setProperty('target_size', content_size)
            img_label.setProperty('image_index', idx)
            
            cache_key = f"{img_path_str}_{content_size}"
            if cache_key in self.thumbnail_cache:
                img_label.setPixmap(self.thumbnail_cache[cache_key])
            else:
                img_label.setPixmap(placeholder_pixmap)
            
            self._apply_grid_item_baseline(img_label)
            img_label.show()
            self.grid_widgets[idx] = img_label
    
    def _queue_visible_thumbnails(self):
        for idx in range(self.visible_start_idx, self.visible_end_idx):
            if idx not in self.grid_widgets:
                continue
            
            widget = self.grid_widgets[idx]
            img_path = widget.property('image_path')
            target_size = widget.property('target_size')
            
            if not img_path:
                continue
            
            cache_key = f"{img_path}_{target_size}"
            if cache_key not in self.thumbnail_cache and (img_path, target_size) not in self.thumbnail_queue:
                self.thumbnail_queue.append((img_path, target_size))
        
        if self.thumbnail_queue and not self.load_timer.isActive():
            self.loading_changed.emit(True)
            self.load_timer.start(5)
    
    def _on_grid_scroll(self):
        current_scroll = self.scroll_area.verticalScrollBar().value()
        self.scroll_direction = 1 if current_scroll >= self.last_scroll_y else -1
        self.last_scroll_y = current_scroll
        
        self._update_visible_grid_range()
        
        self.preload_timer.start(50)

    def _on_grid_item_double_clicked(self, path_str: str):
        if path_str and self.preview_overlay:
            self.preview_overlay.show_image(path_str)

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
        
        self._cancel_all_thumbnail_threads()
        
        if self.images:
            if mode == 'list':
                self._populate_list_view()
            elif mode == 'grid':
                self._populate_grid_view()
            elif mode == 'details':
                self._populate_details_view()
            
            if self.current_search_query:
                QTimer.singleShot(100, lambda q=self.current_search_query: self.search_and_highlight(q))
    
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
            self._rebuild_grid_virtual()
    
    def _load_next_thumbnail(self):
        if not self.thumbnail_queue:
            self.loading_changed.emit(False)
            return
        
        active_count = len([t for t in self.active_thumbnail_threads if t.isRunning()])
        
        while self.thumbnail_queue and active_count < self.MAX_CONCURRENT_THUMBNAILS:
            img_path, size = self.thumbnail_queue.pop(0)
            
            cache_key = f"{img_path}_{size}"
            if cache_key in self.thumbnail_cache:
                continue
            
            thread = ThumbnailLoaderThread(img_path, size)
            thread.thumbnail_ready.connect(self._on_thumbnail_ready)
            thread.finished.connect(lambda t=thread: self._cleanup_thumbnail_thread(t))
            self.active_thumbnail_threads.append(thread)
            thread.start()
            active_count += 1
        
        if self.thumbnail_queue:
            self.load_timer.start(5)
        elif active_count == 0:
            self.loading_changed.emit(False)
    
    def _on_thumbnail_ready(self, img_path, size, pixmap):
        cache_key = f"{img_path}_{size}"
        self.thumbnail_cache[cache_key] = pixmap
        
        if self.current_view == 'list':
            for i in range(self.list_view.count()):
                item = self.list_view.item(i)
                if item and item.data(Qt.UserRole) == img_path:
                    item.setIcon(QIcon(pixmap))
                    break
        elif self.current_view == 'grid':
            for idx, widget in self.grid_widgets.items():
                if widget.property('image_path') == img_path:
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
        self._clear_grid_widgets()
        self.table_view.setRowCount(0)
        self.images = []
        self.visible_start_idx = 0
        self.visible_end_idx = 0
    
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
                
                for i in range(self.list_view.count()):
                    item = self.list_view.item(i)
                    if not item:
                        continue
                    name = item.text().lower()
                    if q in name:
                        item.setBackground(QBrush(highlight_color))
                    else:
                        item.setBackground(clear_brush)
                
                if first_match_index >= 0 and first_match_index < self.list_view.count():
                    item = self.list_view.item(first_match_index)
                    if item:
                        self.list_view.scrollToItem(item)
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
                
                if first_match_index >= 0 and self.item_height > 0:
                    target_row = first_match_index // self.grid_width
                    scroll_y = target_row * self.item_height
                    self.scroll_area.verticalScrollBar().setValue(scroll_y)
                    QTimer.singleShot(50, self._update_visible_grid_range)
                
                QTimer.singleShot(100, lambda: self._apply_search_highlight_grid(q))
            else:
                for idx, widget in self.grid_widgets.items():
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
    
    def _apply_search_highlight_grid(self, query):
        for idx, widget in self.grid_widgets.items():
            img_path = widget.property('image_path')
            name = Path(img_path).name.lower() if img_path else ''
            if query in name:
                self._apply_grid_item_highlight(widget)
            else:
                self._apply_grid_item_baseline(widget)
