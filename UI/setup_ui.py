from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication
from Configs.configs_file_manager import load_config as load_app_config, load_env, load_menu_config
from UI.Widgets.status_bar_widget import StatusBar
from UI.Widgets.menu_bar_widget import MenuBar
from UI.Widgets.ToolBarWidget.navigation_toolbar_widget import NavigationToolbarWidget
from UI.Widgets.ToolBarWidget.action_toolbar_widget import ActionToolbarWidget
from UI.Widgets.SideBarWidget.sidebar_widget import Sidebar
from UI.Widgets.CentralWidget.central_widget import CentralWidget
from UI.Assets.assets_manager import get_icon
import sys
import ctypes
import re


def _set_windows_app_user_model_id(cfg: dict):
    name = cfg["name"]
    safe = re.sub(r'[^A-Za-z0-9]', '', name).lower()
    appid = f"com.{safe}"
    if sys.platform == "win32":
        res = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(ctypes.c_wchar_p(appid))
        if res != 0:
            raise OSError(f"SetCurrentProcessExplicitAppUserModelID failed with code {res}")


def apply_app_metadata(app: QApplication, base_path: Path):
    cfg = load_app_config(base_path)
    app.setApplicationName(cfg["name"])
    app.setApplicationVersion(cfg["version"])
    app.setProperty("license", cfg["license"])
    icon = get_icon("app_icon.ico", base_path)
    app.setWindowIcon(icon)
    if sys.platform == "win32":
        _set_windows_app_user_model_id(cfg)


def center_on_screen(window):
    screen = window.screen() or QGuiApplication.primaryScreen()
    available = screen.availableGeometry()
    frame = window.frameGeometry()
    frame.moveCenter(available.center())
    window.move(frame.topLeft())


def apply_window_metadata(window, base_path: Path):
    cfg = load_app_config(base_path)
    name = cfg["name"]
    version = cfg["version"]
    status = cfg["status"]
    if status:
        window.setWindowTitle(f"{name} {version} ({status})")
    else:
        window.setWindowTitle(f"{name} {version}")
    window.setProperty("name", name)
    window.setProperty("version", version)
    window.setProperty("status", status)
    window_cfg = cfg["window"]
    window.setMinimumSize(window_cfg["min_width"], window_cfg["min_height"])
    env = load_env(base_path)
    development = env["DEVELOPMENT"] == "True"
    statusbar = StatusBar(cfg, development)
    window.setStatusBar(statusbar)
    menu_cfg = load_menu_config(base_path)
    menubar = MenuBar(menu_cfg, base_path, parent=window)
    window.setMenuBar(menubar)
    nav_toolbar = NavigationToolbarWidget(base_path, parent=window)
    action_toolbar = ActionToolbarWidget(base_path, parent=window)
    search_toolbar = None
    settings_toolbar = None

    sidebar = Sidebar(base_path, parent=window)

    central = CentralWidget(parent=window)
    old = sidebar.content
    old.setParent(None)
    old.deleteLater()
    sidebar.content = central
    sidebar.splitter.addWidget(central)
    sidebar.splitter.setCollapsible(1, False)
    sidebar.splitter.setStretchFactor(1, 1)

    window.setCentralWidget(sidebar)

    # instantiate optional toolbars (kept separate in case of missing Qt availability)
    from UI.Widgets.ToolBarWidget.search_toolbar_widget import SearchToolbarWidget
    from UI.Widgets.ToolBarWidget.settings_toolbar_widget import SettingsToolbarWidget
    search_toolbar = SearchToolbarWidget(base_path, parent=window)
    settings_toolbar = SettingsToolbarWidget(base_path, parent=window)

    # add all toolbars (hidden by default); manager will control visibility
    window.addToolBar(nav_toolbar)
    window.addToolBar(action_toolbar)
    window.addToolBar(search_toolbar)
    window.addToolBar(settings_toolbar)
    nav_toolbar.setVisible(False)
    action_toolbar.setVisible(False)
    search_toolbar.setVisible(False)
    settings_toolbar.setVisible(False)

    # centralize connections in a manager
    from UI.Widgets.widget_connection_manager import WidgetConnectionManager
    manager = WidgetConnectionManager(parent=window)
    manager.setup(window, sidebar, nav_toolbar=nav_toolbar, action_toolbar=action_toolbar, search_toolbar=search_toolbar, settings_toolbar=settings_toolbar)

    return sidebar

