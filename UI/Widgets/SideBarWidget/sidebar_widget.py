from pathlib import Path
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QFrame, QSplitter, QSizePolicy, QLabel
import qtawesome as qta
from UI.Themes.papika_global_themes import PAPIKA_THEME
from UI.Widgets.SideBarWidget.sidebar_navigation_widget import SidebarNavigationWidget
from UI.Widgets.SideBarWidget.sidebar_navigation_details_widget import SidebarNavigationDetailsWidget
from UI.Widgets.SideBarWidget.sidebar_action_widget import SidebarActionWidget
from UI.Widgets.SideBarWidget.sidebar_action_details_widget import SidebarActionDetailsWidget
from UI.Widgets.SideBarWidget.sidebar_sorting_widget import SidebarSortingWidget
from UI.Widgets.SideBarWidget.sidebar_sorting_details_widget import SidebarSortingDetailsWidget
from UI.Widgets.SideBarWidget.sidebar_search_widget import SidebarSearchWidget
from UI.Widgets.SideBarWidget.sidebar_search_details_widget import SidebarSearchDetailsWidget
from UI.Widgets.SideBarWidget.sidebar_settings_widget import SidebarSettingsWidget
from UI.Widgets.SideBarWidget.sidebar_settings_details_widget import SidebarSettingsDetailsWidget

class Sidebar(QWidget):
    active_tab_changed = Signal(str)

    def __init__(self, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        
        self.colors = PAPIKA_THEME.get_colors()
        self.sizes = PAPIKA_THEME.get_sizes()
        self.spacing = PAPIKA_THEME.get_spacing()
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(*self.spacing['margins_none'])
        main_layout.setSpacing(0)
        
        self.permanent_sidebar = QFrame()
        self.permanent_sidebar.setObjectName("permanent_sidebar")
        self.permanent_sidebar.setFixedWidth(self.sizes['sidebar_width'])
        self.permanent_sidebar.setFrameShape(QFrame.StyledPanel)
        
        perm_layout = QVBoxLayout(self.permanent_sidebar)
        perm_layout.setContentsMargins(0, self.spacing['spacing_small'], 0, self.spacing['spacing_small'])
        perm_layout.setSpacing(self.spacing['spacing_small'])
        perm_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        
        self.toggle_button = QPushButton()
        self.toggle_button.setIcon(qta.icon("fa6s.bars"))
        PAPIKA_THEME.apply_sidebar_button_style(self.toggle_button)
        self.toggle_button.setToolTip("Toggle Sidebar")
        self.toggle_button.clicked.connect(self.toggle_sidebar)
        perm_layout.addWidget(self.toggle_button, 0, Qt.AlignCenter)
        
        self.btn_files = QPushButton()
        self.btn_files.setIcon(qta.icon("fa6s.folder", color=self.colors['icon_inactive']))
        PAPIKA_THEME.apply_sidebar_button_style(self.btn_files)
        self.btn_files.setToolTip("Files")
        self.btn_files.clicked.connect(lambda: self.set_active_tab('files'))
        perm_layout.addWidget(self.btn_files, 0, Qt.AlignCenter)
        
        self.btn_play = QPushButton()
        self.btn_play.setIcon(qta.icon("fa6s.play", color=self.colors['icon_inactive']))
        PAPIKA_THEME.apply_sidebar_button_style(self.btn_play)
        self.btn_play.setToolTip("Play")
        self.btn_play.clicked.connect(lambda: self.set_active_tab('play'))
        perm_layout.addWidget(self.btn_play, 0, Qt.AlignCenter)

        self.btn_sorting = QPushButton()
        self.btn_sorting.setIcon(qta.icon("fa6s.arrow-down-a-z", color=self.colors['icon_inactive']))
        PAPIKA_THEME.apply_sidebar_button_style(self.btn_sorting)
        self.btn_sorting.setToolTip("Sorting")
        self.btn_sorting.clicked.connect(lambda: self.set_active_tab('sorting'))
        perm_layout.addWidget(self.btn_sorting, 0, Qt.AlignCenter)

        self.btn_search = QPushButton()
        self.btn_search.setIcon(qta.icon("fa6s.magnifying-glass", color=self.colors['icon_inactive']))
        PAPIKA_THEME.apply_sidebar_button_style(self.btn_search)
        self.btn_search.setToolTip("Search")
        self.btn_search.clicked.connect(lambda: self.set_active_tab('search'))
        perm_layout.addWidget(self.btn_search, 0, Qt.AlignCenter)

        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(qta.icon("fa6s.gear", color=self.colors['icon_inactive']))
        PAPIKA_THEME.apply_sidebar_button_style(self.btn_settings)
        self.btn_settings.setToolTip("Settings")
        self.btn_settings.clicked.connect(lambda: self.set_active_tab('settings'))
        perm_layout.addWidget(self.btn_settings, 0, Qt.AlignCenter)
        
        perm_layout.addStretch()
        
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.collapsible_sidebar = QFrame()
        self.collapsible_sidebar.setObjectName("collapsible_sidebar")
        self.collapsible_sidebar.setMinimumWidth(self.sizes['sidebar_min_width'])
        self.collapsible_sidebar.setFrameShape(QFrame.StyledPanel)
        
        coll_layout = QVBoxLayout(self.collapsible_sidebar)
        coll_layout.setContentsMargins(*self.spacing['margins_none'])
        coll_layout.setSpacing(0)
        
        self.header_label = QLabel('Files')
        self.header_label.setObjectName('sidebar_header')
        self.header_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.header_label.setStyleSheet(PAPIKA_THEME.get_stylesheet_header(self.colors['primary']))
        self.header_label.setMinimumHeight(self.sizes['header_height'])
        coll_layout.addWidget(self.header_label, 0)
        
        self.navigation = SidebarNavigationWidget(self.base_path)
        self.navigation.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        coll_layout.addWidget(self.navigation, 1)
        
        self.navigation_details = SidebarNavigationDetailsWidget()
        self.navigation_details.setMinimumHeight(120)
        self.navigation_details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        coll_layout.addWidget(self.navigation_details, 0)
        
        self.action_widget = SidebarActionWidget()
        self.action_widget.hide()
        self.action_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        coll_layout.addWidget(self.action_widget, 1)
        
        self.action_details = SidebarActionDetailsWidget()
        self.action_details.hide()
        self.action_details.setMinimumHeight(120)
        self.action_details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        coll_layout.addWidget(self.action_details, 0)
        
        self.sorting_widget = SidebarSortingWidget()
        self.sorting_widget.hide()
        self.sorting_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        coll_layout.addWidget(self.sorting_widget, 1)
        
        self.sorting_details = SidebarSortingDetailsWidget()
        self.sorting_details.hide()
        self.sorting_details.setMinimumHeight(120)
        self.sorting_details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        coll_layout.addWidget(self.sorting_details, 0)
        
        self.search_widget = SidebarSearchWidget()
        self.search_widget.hide()
        self.search_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        coll_layout.addWidget(self.search_widget, 1)
        
        self.search_details = SidebarSearchDetailsWidget()
        self.search_details.hide()
        self.search_details.setMinimumHeight(100)
        self.search_details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        coll_layout.addWidget(self.search_details, 0)
        
        self.settings_widget = SidebarSettingsWidget()
        self.settings_widget.hide()
        self.settings_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        coll_layout.addWidget(self.settings_widget, 1)
        
        self.settings_details = SidebarSettingsDetailsWidget()
        self.settings_details.hide()
        self.settings_details.setMinimumHeight(100)
        self.settings_details.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        coll_layout.addWidget(self.settings_details, 0)
        
        self.navigation.path_selected.connect(self.navigation_details.update_path)
        self.navigation.loading_changed.connect(self.navigation_details.show_loading)
        self.navigation.path_selected.connect(self.action_widget.set_current_directory)
        self.navigation.path_selected.connect(self.action_details.set_current_directory)
        self.action_widget.scan_completed.connect(self.action_details.update_from_scan_result)

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
        self.btn_files.setIcon(qta.icon("fa6s.folder", color=self.colors['icon_active'] if tab_name == 'files' else self.colors['icon_inactive']))
        self.btn_search.setIcon(qta.icon("fa6s.magnifying-glass", color=self.colors['icon_active'] if tab_name == 'search' else self.colors['icon_inactive']))
        self.btn_play.setIcon(qta.icon("fa6s.play", color=self.colors['secondary'] if tab_name == 'play' else self.colors['icon_inactive']))
        self.btn_sorting.setIcon(qta.icon("fa6s.arrow-down-a-z", color=self.colors['icon_active'] if tab_name == 'sorting' else self.colors['icon_inactive']))
        self.btn_settings.setIcon(qta.icon("fa6s.gear", color=self.colors['icon_active'] if tab_name == 'settings' else self.colors['icon_inactive']))
        if tab_name == 'files':
            self.header_label.setText('Files')
            self.navigation.show()
            self.navigation_details.show()
            self.action_widget.hide()
            self.action_details.hide()
            self.sorting_widget.hide()
            self.sorting_details.hide()
            self.search_widget.hide()
            self.search_details.hide()
            self.settings_widget.hide()
            self.settings_details.hide()
        elif tab_name == 'play':
            self.header_label.setText('Actions')
            self.navigation.hide()
            self.navigation_details.hide()
            self.action_widget.show()
            self.action_details.show()
            self.sorting_widget.hide()
            self.sorting_details.hide()
            self.search_widget.hide()
            self.search_details.hide()
            self.settings_widget.hide()
            self.settings_details.hide()
        elif tab_name == 'sorting':
            self.header_label.setText('Sorting')
            self.navigation.hide()
            self.navigation_details.hide()
            self.action_widget.hide()
            self.action_details.hide()
            self.sorting_widget.show()
            self.sorting_details.show()
            self.search_widget.hide()
            self.search_details.hide()
            self.settings_widget.hide()
            self.settings_details.hide()
        elif tab_name == 'search':
            self.header_label.setText('Search')
            self.navigation.hide()
            self.navigation_details.hide()
            self.action_widget.hide()
            self.action_details.hide()
            self.sorting_widget.hide()
            self.sorting_details.hide()
            self.search_widget.show()
            self.search_details.show()
            self.settings_widget.hide()
            self.settings_details.hide()
        elif tab_name == 'settings':
            self.header_label.setText('Settings')
            self.navigation.hide()
            self.navigation_details.hide()
            self.action_widget.hide()
            self.action_details.hide()
            self.sorting_widget.hide()
            self.sorting_details.hide()
            self.search_widget.hide()
            self.search_details.hide()
            self.settings_widget.show()
            self.settings_details.show()
        else:
            self.header_label.setText('')
            self.navigation.hide()
            self.navigation_details.hide()
            self.action_widget.hide()
            self.action_details.hide()
            self.sorting_widget.hide()
            self.sorting_details.hide()
            self.search_widget.hide()
            self.search_details.hide()
            self.settings_widget.hide()
            self.settings_details.hide()
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
