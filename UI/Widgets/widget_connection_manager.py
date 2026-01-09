from typing import Optional
from PySide6.QtCore import QObject


class WidgetConnectionManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = None
        self.sidebar = None
        self.nav_toolbar = None
        self.action_toolbar = None

    def setup(self, window, sidebar, nav_toolbar=None, action_toolbar=None, search_toolbar=None, settings_toolbar=None, sorting_toolbar=None):
        self.window = window
        self.sidebar = sidebar
        self.nav_toolbar = nav_toolbar
        self.action_toolbar = action_toolbar
        self.search_toolbar = search_toolbar
        self.settings_toolbar = settings_toolbar
        self.sorting_toolbar = sorting_toolbar
        self.central_manager = None

        central = sidebar.content if hasattr(sidebar, 'content') else None
        
        if nav_toolbar and hasattr(sidebar, 'navigation') and sidebar.navigation:
            nav = sidebar.navigation
            nav.path_selected.connect(nav_toolbar.update_path)
            nav_toolbar.path_changed.connect(lambda path, n=nav: n.navigate_to_path(path) if path else None)
            nav_toolbar.path_changed.connect(lambda p, m=central.manager: m.load_path(p) if hasattr(m, 'load_path') else None)
            nav_toolbar.refresh_requested.connect(nav.refresh_tree)
            
            if central and hasattr(central, 'manager'):
                self.central_manager = central.manager
                nav.path_selected.connect(central.manager.load_path)
                nav_toolbar.view_mode_changed.connect(central.manager.set_view_mode)
                nav_toolbar.view_mode_changed.connect(lambda mode, nt=nav_toolbar, m=central.manager: m.search(nt.search_field.text().strip()) if nt.search_field.text().strip() else None)
                nav_toolbar.sort_changed.connect(central.manager.set_sort)
                nav_toolbar.grid_width_changed.connect(central.manager.set_grid_width)
                nav_toolbar.search_triggered.connect(lambda q, m=central.manager: m.search(q) if hasattr(m, 'search') else None)
                central.manager.extensions_found.connect(nav_toolbar.update_extensions)
                central.manager.loading_changed.connect(sidebar.navigation_details.show_loading)
                central.manager.loaded_count_changed.connect(sidebar.navigation_details.update_loaded_count)

        if action_toolbar and hasattr(sidebar, 'navigation') and sidebar.navigation:
            nav = sidebar.navigation
            nav.path_selected.connect(action_toolbar.update_path)
            action_toolbar.path_changed.connect(lambda path, n=nav: n.navigate_to_path(path) if path else None)
            action_toolbar.path_changed.connect(lambda p, m=central.manager: m.load_path(p) if hasattr(m, 'load_path') else None)
            action_toolbar.refresh_requested.connect(nav.refresh_tree)

            action_toolbar.path_changed.connect(lambda p, a=sidebar.action_widget: a.set_current_directory(p) if hasattr(a, 'set_current_directory') else None)
            action_toolbar.path_changed.connect(lambda p, d=sidebar.action_details: d.set_current_directory(p) if hasattr(d, 'set_current_directory') else None)

        if search_toolbar:
            search_toolbar.search_requested.connect(lambda q: self._show_status(f"Search: {q}", 1500))

        if settings_toolbar:
            settings_toolbar.reload_requested.connect(lambda: self._show_status('Settings reloaded', 1500))

        if sorting_toolbar and hasattr(sidebar, 'sorting_widget'):
            sorting_toolbar.sort_requested.connect(lambda order: self._show_status(f"Sort {order}", 1500))
            sorting_toolbar.filter_requested.connect(lambda: self._show_status('Filter', 1500))
            sorting_toolbar.group_requested.connect(lambda: self._show_status('Group', 1500))

        if search_toolbar:
            search_toolbar.search_requested.connect(lambda q: self._show_status(f"Search: {q}", 1500))

        if settings_toolbar:
            settings_toolbar.reload_requested.connect(lambda: self._show_status('Settings reloaded', 1500))

        sidebar.active_tab_changed.connect(self._on_tab_changed)
        self._on_tab_changed(sidebar._active_tab)

    def _on_tab_changed(self, tab_name: str):
        if self.nav_toolbar:
            self.nav_toolbar.setVisible(tab_name == 'files')
        if self.action_toolbar:
            self.action_toolbar.setVisible(tab_name in ('play', 'run'))
        if hasattr(self, 'search_toolbar') and self.search_toolbar:
            self.search_toolbar.setVisible(tab_name == 'search')
        if hasattr(self, 'settings_toolbar') and self.settings_toolbar:
            self.settings_toolbar.setVisible(tab_name == 'settings')
        if hasattr(self, 'sorting_toolbar') and self.sorting_toolbar:
            self.sorting_toolbar.setVisible(tab_name == 'sorting')
        self._show_status(f"Active tab: {tab_name}", 400)
        if tab_name in ('files', 'search') and self.nav_toolbar and self.central_manager:
            q = self.nav_toolbar.search_field.text().strip()
            if q:
                self.central_manager.search(q)

    def _show_status(self, text: str, timeout: int = 2000):
        try:
            sb = self.window.statusBar() if self.window else None
            if sb is None:
                return
            if hasattr(sb, 'show_temporary'):
                sb.show_temporary(text, timeout)
            else:
                sb.showMessage(text, timeout)
        except Exception as e:
            print(f"Error disconnecting widget connections: {e}")
