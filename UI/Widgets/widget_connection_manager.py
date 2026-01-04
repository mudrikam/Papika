from typing import Optional
from PySide6.QtCore import QObject


class WidgetConnectionManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = None
        self.sidebar = None
        self.nav_toolbar = None
        self.action_toolbar = None

    def setup(self, window, sidebar, nav_toolbar=None, action_toolbar=None, search_toolbar=None, settings_toolbar=None):
        self.window = window
        self.sidebar = sidebar
        self.nav_toolbar = nav_toolbar
        self.action_toolbar = action_toolbar
        self.search_toolbar = search_toolbar
        self.settings_toolbar = settings_toolbar

        if nav_toolbar and hasattr(sidebar, 'navigation') and sidebar.navigation:
            nav = sidebar.navigation
            nav.path_selected.connect(nav_toolbar.update_path)
            nav_toolbar.path_changed.connect(lambda path: nav.path_input.setText(path))
            nav_toolbar.path_changed.connect(lambda path: nav.navigate_to_path())
            nav_toolbar.refresh_requested.connect(nav.refresh_tree)

        if action_toolbar:
            # when run is triggered from toolbar, switch to play tab
            action_toolbar.run_requested.connect(lambda: self.sidebar.set_active_tab('play'))
            action_toolbar.stop_requested.connect(lambda: self._show_status('Stop requested', 1500))

        if search_toolbar:
            # search toolbar emits search_requested; for now show status when used
            search_toolbar.search_requested.connect(lambda q: self._show_status(f"Search: {q}", 1500))

        if settings_toolbar:
            settings_toolbar.reload_requested.connect(lambda: self._show_status('Settings reloaded', 1500))

        # centralize active tab handling
        sidebar.active_tab_changed.connect(self._on_tab_changed)
        # apply initial state
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
        # set play icon color via sidebar (sidebar handles this), ensure status reflects change
        self._show_status(f"Active tab: {tab_name}", 400)

    def _show_status(self, text: str, timeout: int = 2000):
        try:
            sb = self.window.statusBar() if self.window else None
            if sb is None:
                return
            if hasattr(sb, 'show_temporary'):
                sb.show_temporary(text, timeout)
            else:
                sb.showMessage(text, timeout)
        except Exception:
            pass
