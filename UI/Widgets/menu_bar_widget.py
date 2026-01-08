
from pathlib import Path
from PySide6.QtWidgets import QMenuBar, QMenu, QApplication
from PySide6.QtGui import QAction
import qtawesome as qta
from UI.Assets.assets_manager import get_icon
from UI.Dialogs.about_dialog import show_about
from UI.Dialogs.license_dialog import show_license
import webbrowser
from Configs.configs_file_manager import load_config
import os
import sys

class MenuBar(QMenuBar):
    def __init__(self, menu_cfg: dict, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        self.links = load_config(base_path).get("links", {})
        self._setup_role_handlers()
        for mcfg in menu_cfg.get("menus", []):
            if mcfg.get("direct_action"):
                self._create_direct_action_menu(mcfg)
            else:
                self._create_submenu(mcfg)

    def _setup_role_handlers(self):
        self.role_handlers = {
            "quit": QApplication.quit,
            "relaunch": self._relaunch_app,
            "about": lambda: show_about(self.parentWidget(), self.base_path),
            "license": lambda: show_license(self.parentWidget(), self.base_path),
            "whatsapp": lambda: webbrowser.open(self.links.get("whatsapp")),
            "tiktok": lambda: webbrowser.open(self.links.get("tiktok")),
            "readme": lambda: webbrowser.open(self.links.get("readme")),
            "telegram": lambda: webbrowser.open(self.links.get("telegram")),
            "repo": lambda: webbrowser.open(self.links.get("repo"))
        }

    def _get_icon(self, icon_name: str):
        if not icon_name:
            return None
        if icon_name.startswith("fa"):
            return qta.icon(icon_name)
        return get_icon(icon_name, self.base_path)

    def _create_action(self, label: str, icon_name: str = None, shortcut: str = None, role: str = None):
        icon = self._get_icon(icon_name)
        action = QAction(icon, label, self) if icon else QAction(label, self)
        if shortcut:
            action.setShortcut(shortcut)
        if role and role in self.role_handlers:
            action.triggered.connect(self.role_handlers[role])
        return action

    def _create_submenu(self, menu_config: dict):
        menu = QMenu(menu_config["title"], self)
        for item in menu_config.get("items", []):
            action = self._create_action(
                label=item["label"],
                icon_name=item.get("icon"),
                shortcut=item.get("shortcut"),
                role=item.get("role")
            )
            menu.addAction(action)
        self.addMenu(menu)

    def _create_direct_action_menu(self, menu_config: dict):
        action = self._create_action(
            label=menu_config["title"],
            icon_name=menu_config.get("icon"),
            role=menu_config.get("role")
        )
        self.addAction(action)

    def _relaunch_app(self):
        os.execv(sys.executable, [sys.executable] + sys.argv)
