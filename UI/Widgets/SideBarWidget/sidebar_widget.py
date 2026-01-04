from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFrame, QSplitter
import qtawesome as qta
from UI.Widgets.SideBarWidget.sidebar_navigation_widget import SidebarNavigationWidget
from UI.Widgets.SideBarWidget.sidebar_details_widget import SidebarDetailsWidget

class Sidebar(QWidget):
    active_tab_changed = Signal(str)

    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(0)
        
        self.permanent_sidebar = QFrame()
        self.permanent_sidebar.setObjectName("permanent_sidebar")
        self.permanent_sidebar.setFixedWidth(50)
        self.permanent_sidebar.setFrameShape(QFrame.StyledPanel)
        
        perm_layout = QVBoxLayout(self.permanent_sidebar)
        perm_layout.setContentsMargins(0, 5, 0, 5)
        perm_layout.setSpacing(5)
        perm_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        
        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(qta.icon("fa6s.bars"))
        self.toggle_button.setFixedSize(40, 40)
        self.toggle_button.setFlat(True)
        self.toggle_button.setToolTip("Toggle Sidebar")
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        perm_layout.addWidget(self.toggle_button, 0, Qt.AlignCenter)
        
        # Permanent tab buttons (use inactive color by default)
        self._perm_active_color = '#f7a128'
        self._perm_inactive_color = '#9CA3AF'

        self.btn_files = QPushButton()
        self.btn_files.setIcon(qta.icon("fa6s.folder", color=self._perm_inactive_color))
        self.btn_files.setFixedSize(40, 40)
        self.btn_files.setFlat(True)
        self.btn_files.setToolTip("Files")
        self.btn_files.clicked.connect(lambda: self.set_active_tab('files'))
        perm_layout.addWidget(self.btn_files, 0, Qt.AlignCenter)
        
        self.btn_search = QPushButton()
        self.btn_search.setIcon(qta.icon("fa6s.magnifying-glass", color=self._perm_inactive_color))
        self.btn_search.setFixedSize(40, 40)
        self.btn_search.setFlat(True)
        self.btn_search.setToolTip("Search")
        self.btn_search.clicked.connect(lambda: self.set_active_tab('search'))
        perm_layout.addWidget(self.btn_search, 0, Qt.AlignCenter)
        
        # Play / Run button (green when active)
        self._perm_play_color = '#16A34A'
        self.btn_play = QPushButton()
        self.btn_play.setIcon(qta.icon("fa6s.play", color=self._perm_inactive_color))
        self.btn_play.setFixedSize(40, 40)
        self.btn_play.setFlat(True)
        self.btn_play.setToolTip("Play")
        self.btn_play.clicked.connect(lambda: self.set_active_tab('play'))
        perm_layout.addWidget(self.btn_play, 0, Qt.AlignCenter)

        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(qta.icon("fa6s.gear", color=self._perm_inactive_color))
        self.btn_settings.setFixedSize(40, 40)
        self.btn_settings.setFlat(True)
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.clicked.connect(lambda: self.set_active_tab('settings'))
        perm_layout.addWidget(self.btn_settings, 0, Qt.AlignCenter)
        
        perm_layout.addStretch()
        
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.collapsible_sidebar = QFrame()
        self.collapsible_sidebar.setObjectName("collapsible_sidebar")
        self.collapsible_sidebar.setMinimumWidth(150)
        self.collapsible_sidebar.setFrameShape(QFrame.StyledPanel)
        
        coll_layout = QVBoxLayout(self.collapsible_sidebar)
        coll_layout.setContentsMargins(0, 0, 0, 0)
        coll_layout.setSpacing(0)
        
        self.navigation = SidebarNavigationWidget(self.base_path)
        coll_layout.addWidget(self.navigation, 1)
        
        self.details = SidebarDetailsWidget()
        self.details.setMinimumHeight(120)
        self.details.setMaximumHeight(150)
        coll_layout.addWidget(self.details, 0)
        
        self.navigation.path_selected.connect(self.details.update_path)

        # Active tab state: 'files' | 'search' | 'settings' etc.
        self._active_tab = None
        self.set_active_tab('files')

        self.content = QWidget()
        self.content.setObjectName("main_content")
        
        self.splitter.addWidget(self.collapsible_sidebar)
        self.splitter.addWidget(self.content)
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(self.permanent_sidebar)
        main_layout.addWidget(self.splitter, 1)
        
        self.is_collapsed = False

    def set_active_tab(self, tab_name: str):
        if tab_name == self._active_tab:
            return
        self._active_tab = tab_name
        # update icons
        self.btn_files.setIcon(qta.icon("fa6s.folder", color=self._perm_active_color if tab_name == 'files' else self._perm_inactive_color))
        self.btn_search.setIcon(qta.icon("fa6s.magnifying-glass", color=self._perm_active_color if tab_name == 'search' else self._perm_inactive_color))
        self.btn_play.setIcon(qta.icon("fa6s.play", color=self._perm_play_color if tab_name == 'play' else self._perm_inactive_color))
        self.btn_settings.setIcon(qta.icon("fa6s.gear", color=self._perm_active_color if tab_name == 'settings' else self._perm_inactive_color))
        # show/hide content for tabs
        if tab_name == 'files':
            self.navigation.show()
            self.details.show()
        else:
            self.navigation.hide()
            self.details.hide()
        # emit change
        self.active_tab_changed.emit(tab_name)
    
    def start_navigation_init(self, progress_callback=None):
        self.navigation.start_initialization(progress_callback)
    
    def toggle_sidebar(self):
        if self.is_collapsed:
            self.collapsible_sidebar.show()
            self.toggle_button.setIcon(qta.icon("fa6s.bars"))
            self.is_collapsed = False
        else:
            self.collapsible_sidebar.hide()
            self.toggle_button.setIcon(qta.icon("fa6s.angles-right"))
            self.is_collapsed = True
