import os
import platform
import time
from pathlib import Path
from PySide6.QtCore import Qt, QDir, QThread, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QApplication, QMessageBox
import qtawesome as qta
from UI.Widgets.SideBarWidget.sidebar_navigation_widget_context_menu import SidebarNavigationContextMenu

class DirectoryScanThread(QThread):
    finished = Signal(list)
    
    def __init__(self, path_str):
        super().__init__()
        self.path_str = path_str
    
    def run(self):
        try:
            path = Path(self.path_str)
            if not path.exists() or not path.is_dir():
                self.finished.emit([])
                return
            
            entries = []
            try:
                entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except (PermissionError, OSError):
                pass
            
            self.finished.emit(entries)
        except Exception as e:
            print(f"Error scanning directory {self.path_str}: {e}")
            self.finished.emit([])

class InitializationThread(QThread):
    progress = Signal(str)
    finished = Signal()
    
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
    
    def run(self):
        self.progress.emit("Scanning system drives...")
        system_name = platform.system()
        
        if system_name == "Windows":
            self.widget._populate_windows_drives()
        elif system_name == "Darwin":
            self.widget._populate_macos_roots()
        else:
            self.widget._populate_linux_roots()
        
        self.progress.emit("Loading network locations...")
        self.widget._add_network_locations()
        
        self.progress.emit("Ready!")
        self.finished.emit()

class SidebarNavigationWidget(QWidget):
    path_selected = Signal(str)
    loading_changed = Signal(bool)
    
    MAX_ITEMS_PER_FOLDER = 100
    
    COLOR_MAP = {
        'volumes': '#3B82F6',
        'folder': '#F59E0B',
        'file': '#9CA3AF',
        'system': '#10B981',
        'network': '#6366F1',
        'image': '#7C3AED',
        'video': '#7C3AED',
        'home': '#06B6D4',
        'desktop': '#06D6A0',
        'documents': '#2563EB',
        'downloads': '#16A34A',
        'music': '#F97316',
        'pictures': '#A78BFA',
        'videos': '#DB2777'
    }

    FOLDER_TO_CATEGORY = {
        'home': 'home',
        'desktop': 'desktop',
        'documents': 'documents',
        'downloads': 'downloads',
        'music': 'music',
        'pictures': 'pictures',
        'videos': 'videos'
    }

    def _get_icon(self, name, category=None):
        color = self.COLOR_MAP.get(category, self.COLOR_MAP['file'])
        return qta.icon(name, color=color)

    def get_color_map(self):
        return dict(self.COLOR_MAP)


    def __init__(self, base_path: Path, parent=None, color_map: dict | None = None):
        super().__init__(parent)
        self.base_path = base_path
        if isinstance(color_map, dict):
            self.COLOR_MAP.update(color_map)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(15)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemExpanded.connect(self.on_item_expanded)
        self.tree.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.tree)
        
        self.context_menu_handler = SidebarNavigationContextMenu(self)
        self.context_menu_handler.remove_footprints_requested.connect(self._handle_remove_footprints)
        self.context_menu_handler.scan_requested.connect(self._handle_scan_requested)
        
        self.scan_threads = []
        self.init_thread = None
        self.is_initialized = False
    
    def start_initialization(self, progress_callback=None):
        self.tree.clear()
        self.init_thread = InitializationThread(self)
        if progress_callback:
            self.init_thread.progress.connect(progress_callback)
        self.init_thread.finished.connect(self._on_init_finished)
        self.init_thread.start()
    
    def _on_init_finished(self):
        self.is_initialized = True
        if self.init_thread:
            self.init_thread = None
    
    def populate_tree(self):
        self.tree.clear()
        
        system_name = platform.system()
        
        if system_name == "Windows":
            self._populate_windows_drives()
        elif system_name == "Darwin":
            self._populate_macos_roots()
        else:
            self._populate_linux_roots()
        
        self._add_network_locations()
        self.is_initialized = True
    
    def _populate_windows_drives(self):
        system_section = QTreeWidgetItem(self.tree)
        system_section.setText(0, "System")
        system_section.setIcon(0, self._get_icon("fa6s.computer", "system"))
        system_section.setExpanded(True)
        
        home_path = Path.home()
        
        common_folders = [
            ("Home", home_path, "fa6s.house"),
            ("Desktop", home_path / "Desktop", "fa6s.desktop"),
            ("Documents", home_path / "Documents", "fa6s.file-lines"),
            ("Downloads", home_path / "Downloads", "fa6s.download"),
            ("Music", home_path / "Music", "fa6s.music"),
            ("Pictures", home_path / "Pictures", "fa6s.image"),
            ("Videos", home_path / "Videos", "fa6s.video"),
        ]
        
        for name, folder_path, icon_name in common_folders:
            if folder_path.exists():
                item = QTreeWidgetItem(system_section)
                item.setText(0, name)
                cat = self.FOLDER_TO_CATEGORY.get(name.lower(), 'folder')
                item.setIcon(0, self._get_icon(icon_name, cat))
                item.setData(0, Qt.UserRole, str(folder_path))
                if folder_path.is_dir():
                    try:
                        if any(folder_path.iterdir()):
                            dummy = QTreeWidgetItem(item)
                            dummy.setText(0, "Loading...")
                    except (PermissionError, OSError):
                        pass
        
        volumes_section = QTreeWidgetItem(self.tree)
        volumes_section.setText(0, "Volumes")
        volumes_section.setIcon(0, self._get_icon("fa6s.server", "volumes"))
        volumes_section.setExpanded(True)
        
        drives = QDir.drives()
        for drive_info in drives:
            drive_path = drive_info.absolutePath()
            drive_item = QTreeWidgetItem(volumes_section)
            
            drive_name = drive_path.replace(":/", "").replace("/", "")
            volume_name = self._get_volume_name(drive_path)
            
            if volume_name:
                drive_item.setText(0, f"{volume_name} ({drive_name}:)")
            else:
                drive_item.setText(0, f"Local Disk ({drive_name}:)")
            
            drive_item.setIcon(0, self._get_icon("fa6s.hard-drive", "volumes"))
            drive_item.setData(0, Qt.UserRole, drive_path)
            
            if QDir(drive_path).exists():
                dummy = QTreeWidgetItem(drive_item)
                dummy.setText(0, "Loading...")
    
    def _get_volume_name(self, drive_path):
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            volumeNameBuffer = ctypes.create_unicode_buffer(1024)
            fileSystemNameBuffer = ctypes.create_unicode_buffer(1024)
            serial_number = None
            max_component_length = None
            file_system_flags = None
            
            rc = kernel32.GetVolumeInformationW(
                ctypes.c_wchar_p(drive_path),
                volumeNameBuffer,
                ctypes.sizeof(volumeNameBuffer),
                serial_number,
                max_component_length,
                file_system_flags,
                fileSystemNameBuffer,
                ctypes.sizeof(fileSystemNameBuffer)
            )
            
            if rc:
                return volumeNameBuffer.value
        except Exception:
            pass
        return None
    
    def _populate_macos_roots(self):
        home_item = QTreeWidgetItem(self.tree)
        home_path = str(Path.home())
        home_item.setText(0, "Home")
        home_item.setIcon(0, self._get_icon("fa6s.house", self.FOLDER_TO_CATEGORY.get('home', 'home')))
        home_item.setData(0, Qt.UserRole, home_path)
        dummy = QTreeWidgetItem(home_item)
        dummy.setText(0, "Loading...")
        
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, "Root (/)")
        root_item.setIcon(0, self._get_icon("fa6s.hard-drive", "volumes"))
        root_item.setData(0, Qt.UserRole, "/")
        dummy = QTreeWidgetItem(root_item)
        dummy.setText(0, "Loading...")
        
        volumes_item = QTreeWidgetItem(self.tree)
        volumes_item.setText(0, "Volumes")
        volumes_item.setIcon(0, self._get_icon("fa6s.server", "volumes"))
        volumes_item.setData(0, Qt.UserRole, "/Volumes")
        dummy = QTreeWidgetItem(volumes_item)
        dummy.setText(0, "Loading...")
    
    def _populate_linux_roots(self):
        home_item = QTreeWidgetItem(self.tree)
        home_path = str(Path.home())
        home_item.setText(0, "Home")
        home_item.setIcon(0, self._get_icon("fa6s.house", self.FOLDER_TO_CATEGORY.get('home', 'home')))
        home_item.setData(0, Qt.UserRole, home_path)
        dummy = QTreeWidgetItem(home_item)
        dummy.setText(0, "Loading...")
        
        root_item = QTreeWidgetItem(self.tree)
        root_item.setText(0, "Root (/)")
        root_item.setIcon(0, self._get_icon("fa6s.hard-drive", "volumes"))
        root_item.setData(0, Qt.UserRole, "/")
        dummy = QTreeWidgetItem(root_item)
        dummy.setText(0, "Loading...")
        
        media_path = Path("/media")
        if media_path.exists():
            media_item = QTreeWidgetItem(self.tree)
            media_item.setText(0, "Media")
            media_item.setIcon(0, self._get_icon("fa6s.compact-disc", "volumes"))
            media_item.setData(0, Qt.UserRole, "/media")
            dummy = QTreeWidgetItem(media_item)
            dummy.setText(0, "Loading...")
        
        mnt_path = Path("/mnt")
        if mnt_path.exists():
            mnt_item = QTreeWidgetItem(self.tree)
            mnt_item.setText(0, "Mount")
            mnt_item.setIcon(0, self._get_icon("fa6s.server", "volumes"))
            mnt_item.setData(0, Qt.UserRole, "/mnt")
            dummy = QTreeWidgetItem(mnt_item)
            dummy.setText(0, "Loading...")
    
    def _add_network_locations(self):
        network_item = QTreeWidgetItem(self.tree)
        network_item.setText(0, "Network")
        network_item.setIcon(0, self._get_icon("fa6s.network-wired", "network"))
        network_item.setData(0, Qt.UserRole, "network://")
    
    def on_item_expanded(self, item):
        if item.childCount() == 1 and item.child(0).text(0) == "Loading...":
            path = item.data(0, Qt.UserRole)
            if path and path != "network://":
                self._load_directory_async(item, path)
    
    def _load_directory_async(self, parent_item, path_str):
        self.loading_changed.emit(True)
        thread = DirectoryScanThread(path_str)
        thread.finished.connect(lambda entries: self._populate_entries(parent_item, entries))
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.scan_threads.append(thread)
        thread.start()
    
    def _cleanup_thread(self, thread):
        if thread in self.scan_threads:
            self.scan_threads.remove(thread)
        if len(self.scan_threads) == 0:
            self.loading_changed.emit(False)
    
    def _populate_entries(self, parent_item, entries):
        if parent_item.childCount() == 1 and parent_item.child(0).text(0) == "Loading...":
            parent_item.removeChild(parent_item.child(0))
        
        if not entries:
            return
        
        total_entries = len(entries)
        display_entries = entries[:self.MAX_ITEMS_PER_FOLDER] if total_entries > self.MAX_ITEMS_PER_FOLDER else entries
        
        for entry in display_entries:
            if entry.exists():
                item = QTreeWidgetItem(parent_item)
                item.setText(0, entry.name)
                item.setData(0, Qt.UserRole, str(entry))
                
                if entry.is_dir():
                    dir_name = entry.name.lower()
                    dir_cat = self.FOLDER_TO_CATEGORY.get(dir_name, 'folder')
                    item.setIcon(0, self._get_icon("fa6s.folder", dir_cat))
                    if entry.is_dir():
                        has_children = False
                        try:
                            child_iter = entry.iterdir()
                            first_child = next(child_iter, None)
                            if first_child:
                                has_children = True
                        except (PermissionError, OSError) as e:
                            print(f"Permission denied accessing {entry}: {e}")
                            has_children = False
                        if has_children:
                            dummy = QTreeWidgetItem(item)
                            dummy.setText(0, "Loading...")
                else:
                    suffix = entry.suffix.lower()
                    if suffix in [".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs", ".go", ".rs"]:
                        item.setIcon(0, self._get_icon("fa6s.file-code", "file"))
                    elif suffix in [".txt", ".md", ".rst", ".log"]:
                        item.setIcon(0, self._get_icon("fa6s.file-lines", "file"))
                    elif suffix in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico"]:
                        item.setIcon(0, self._get_icon("fa6s.file-image", "image"))
                    elif suffix in [".pdf"]:
                        item.setIcon(0, self._get_icon("fa6s.file-pdf", "file"))
                    elif suffix in [".zip", ".tar", ".gz", ".rar", ".7z"]:
                        item.setIcon(0, self._get_icon("fa6s.file-zipper", "file"))
                    elif suffix in [".mp3", ".wav", ".ogg", ".flac"]:
                        item.setIcon(0, self._get_icon("fa6s.file-audio", "file"))
                    elif suffix in [".mp4", ".avi", ".mkv", ".mov"]:
                        item.setIcon(0, self._get_icon("fa6s.file-video", "video"))
                    elif suffix in [".xls", ".xlsx", ".csv"]:
                        item.setIcon(0, self._get_icon("fa6s.file-excel", "file"))
                    elif suffix in [".doc", ".docx"]:
                        item.setIcon(0, self._get_icon("fa6s.file-word", "file"))
                    else:
                        item.setIcon(0, self._get_icon("fa6s.file", "file"))
        
        if total_entries > self.MAX_ITEMS_PER_FOLDER:
            remaining = total_entries - self.MAX_ITEMS_PER_FOLDER
            more_item = QTreeWidgetItem(parent_item)
            more_item.setText(0, f"and {remaining} more files...")
            more_item.setIcon(0, self._get_icon("fa6s.ellipsis", "file"))
            more_item.setData(0, Qt.UserRole, None)
            more_item.setDisabled(True)
    
    def refresh_tree(self):
        current_item = self.tree.currentItem()
        
        def refresh_expanded_items(item):
            if item is None:
                root = self.tree.invisibleRootItem()
                for i in range(root.childCount()):
                    refresh_expanded_items(root.child(i))
                return
            
            if item.isExpanded():
                path = item.data(0, Qt.UserRole)
                if path and path != "network://":
                    if item.childCount() == 1 and item.child(0).text(0) == "Loading...":
                        return
                    while item.childCount() > 0:
                        item.removeChild(item.child(0))
                    dummy = QTreeWidgetItem(item)
                    dummy.setText(0, "Loading...")
                    self._load_directory_async(item, path)
                
                for i in range(item.childCount()):
                    refresh_expanded_items(item.child(i))
        
        refresh_expanded_items(None)
        
        if current_item:
            self.tree.scrollToItem(current_item, QTreeWidget.PositionAtTop)
        
        self._show_status('Refreshed', 1500)
    
    def collapse_tree(self):
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            item_text = item.text(0)
            if item_text in ("System", "Volumes"):
                item.setExpanded(True)
                for j in range(item.childCount()):
                    child = item.child(j)
                    self._collapse_recursive(child)
            else:
                self._collapse_recursive(item)
        self._show_status('Tree collapsed', 1500)
    
    def _collapse_recursive(self, item):
        if item is None:
            return
        item.setExpanded(False)
        for i in range(item.childCount()):
            self._collapse_recursive(item.child(i))

    def _show_status(self, text: str, timeout: int = 0):
        try:
            window = self.window()
            if window is None:
                return
            sb = window.statusBar()
            if sb is None:
                return
            if hasattr(sb, 'show_temporary'):
                sb.show_temporary(text, timeout)
            else:
                sb.showMessage(text, timeout)
        except Exception as e:
            print(f"Failed to show status: {e}")
    
    def on_item_clicked(self, item, column):
        path = item.data(0, Qt.UserRole)
        if path and path != "network://":
            self.path_selected.emit(path)
    
    def navigate_to_path(self, path_text):
        if not path_text:
            return

        path = Path(path_text)
        if not path.exists():
            try_path = os.path.normpath(path_text)
            if os.name == 'nt' and len(try_path) == 2 and try_path[1] == ':':
                path = Path(try_path + os.sep)
            else:
                print(f"Path does not exist: {path_text}")
                return

        if path.is_file():
            path = path.parent

        self.path_selected.emit(str(path))

        if not self.is_initialized:
            def _delayed_expand():
                time.sleep(0.05)
                result = self._expand_to_path(path)
                if result:
                    current = self.tree.currentItem()
                    if current:
                        self.tree.scrollToItem(current, QTreeWidget.PositionAtTop)
            self.start_initialization()
            if self.init_thread:
                self.init_thread.finished.connect(_delayed_expand)
            else:
                _delayed_expand()
            return

        result = self._expand_to_path(path)
        if result:
            current = self.tree.currentItem()
            if current:
                self.tree.scrollToItem(current, QTreeWidget.PositionAtTop)

    def _expand_to_path(self, target_path):
        target_str = os.path.normpath(str(target_path)).lower()
        
        def find_and_expand(parent_item, depth=0):
            if parent_item is None:
                root = self.tree.invisibleRootItem()
                for i in range(root.childCount()):
                    item = root.child(i)
                    if find_and_expand(item, depth):
                        return True
                return False
            
            item_path = parent_item.data(0, Qt.UserRole)
            if not item_path or item_path == "network://":
                for i in range(parent_item.childCount()):
                    if find_and_expand(parent_item.child(i), depth + 1):
                        return True
                return False
            
            item_path_norm = os.path.normpath(str(item_path)).lower()
            
            if item_path_norm == target_str:
                self.tree.setCurrentItem(parent_item)
                self.tree.scrollToItem(parent_item, QTreeWidget.PositionAtTop)
                parent_item.setExpanded(True)
                return True
            
            target_with_sep = target_str + os.sep if not target_str.endswith(os.sep) else target_str
            item_with_sep = item_path_norm + os.sep if not item_path_norm.endswith(os.sep) else item_path_norm
            
            if target_with_sep.startswith(item_with_sep):
                if not parent_item.isExpanded():
                    parent_item.setExpanded(True)
                    self.on_item_expanded(parent_item)

                start = time.time()
                while parent_item.childCount() == 1 and parent_item.child(0).text(0) == "Loading...":
                    QApplication.processEvents()
                    if time.time() - start > 10:
                        break
                    time.sleep(0.05)
                
                for i in range(parent_item.childCount()):
                    child = parent_item.child(i)
                    if find_and_expand(child, depth + 1):
                        return True
            
            return False
        
        return find_and_expand(None)
    
    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return
        
        path = item.data(0, Qt.UserRole)
        if not path or path == "network://":
            return
        
        menu = self.context_menu_handler.create_menu(path, self.tree)
        menu.exec_(self.tree.viewport().mapToGlobal(position))
    
    def _handle_remove_footprints(self, path: str):
        try:
            from PapikaCore.papika_directory_operations import remove_footprints
            
            directory_path = Path(path)
            remove_footprints(directory_path, self.base_path)
            
            QMessageBox.information(
                self,
                "Success",
                f"Successfully removed Papika's footprints from:\n{path}"
            )
        except FileNotFoundError as e:
            QMessageBox.warning(
                self,
                "Not Found",
                str(e)
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to remove footprints:\n{str(e)}"
            )
    
    def _handle_scan_requested(self, path: str):
        try:
            # Traverse parents to find Sidebar (which holds action_widget)
            parent_widget = self.parent()
            sidebar = None
            while parent_widget is not None:
                if hasattr(parent_widget, 'action_widget'):
                    sidebar = parent_widget
                    break
                parent_widget = parent_widget.parent()
            
            if sidebar and hasattr(sidebar, 'action_widget'):
                action_widget = sidebar.action_widget
                action_widget.set_current_directory(path)
                action_widget._on_scan_directory_clicked()
                self._show_status(f"Scanning: {Path(path).name}", 1500)
            else:
                # Fallback: select the path so user can scan manually
                self.path_selected.emit(path)
        except Exception as e:
            print(f"Error handling scan request for {path}: {e}")

