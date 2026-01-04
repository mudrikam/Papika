from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication
from Configs.configs_file_manager import load_config as load_app_config, load_env, load_menu_config
from UI.Widgets.status_bar_widget import StatusBar
from UI.Widgets.menu_bar_widget import MenuBar
from UI.Widgets.ToolBarWidget.navigation_toolbar_widget import NavigationToolbarWidget
from UI.Widgets.SideBarWidget.sidebar_widget import Sidebar
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
    toolbar = NavigationToolbarWidget(base_path, parent=window)
    window.addToolBar(toolbar)
    sidebar = Sidebar(base_path, parent=window)
    window.setCentralWidget(sidebar)
    
    if hasattr(sidebar, 'navigation') and sidebar.navigation:
        nav = sidebar.navigation
        nav.path_selected.connect(toolbar.update_path)
        toolbar.path_changed.connect(lambda path: nav.path_input.setText(path))
        toolbar.path_changed.connect(lambda path: nav.navigate_to_path())
        toolbar.refresh_requested.connect(nav.refresh_tree)
    
    return sidebar

