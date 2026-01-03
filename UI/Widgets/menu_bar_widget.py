
from pathlib import Path
from PySide6.QtWidgets import QMenuBar, QMenu, QApplication
from PySide6.QtGui import QAction
import qtawesome as qta
from UI.Assets.assets_manager import get_icon
from UI.Dialogs.about_dialog import show_about
from UI.Dialogs.license_dialog import show_license
import webbrowser
from Configs.configs_file_manager import load_config

class MenuBar(QMenuBar):
    def __init__(self, menu_cfg: dict, base_path: Path, parent=None):
        super().__init__(parent)
        self.base_path = base_path
        self.links = load_config(base_path).get("links", {})
        for mcfg in menu_cfg.get("menus", []):
            menu = QMenu(mcfg["title"], self)
            for item in mcfg.get("items", []):
                label = item["label"]
                icon = None
                icon_name = item.get("icon")
                if icon_name:
                    if icon_name.startswith("fa"):
                        icon = qta.icon(icon_name)
                    else:
                        icon = get_icon(icon_name, base_path)
                act = QAction(icon, label, self) if icon else QAction(label, self)
                shortcut = item.get("shortcut")
                if shortcut:
                    act.setShortcut(shortcut)
                role = item.get("role")
                if role == "quit":
                    act.triggered.connect(QApplication.quit)
                elif role == "about":
                    act.triggered.connect(lambda checked=False: show_about(self.parentWidget(), self.base_path))
                elif role == "license":
                    act.triggered.connect(lambda checked=False: show_license(self.parentWidget(), self.base_path))
                elif role == "whatsapp":
                    act.triggered.connect(lambda checked=False: webbrowser.open(self.links.get("whatsapp")))
                elif role == "tiktok":
                    act.triggered.connect(lambda checked=False: webbrowser.open(self.links.get("tiktok")))
                elif role == "readme":
                    act.triggered.connect(lambda checked=False: webbrowser.open(self.links.get("readme")))
                elif role == "telegram":
                    act.triggered.connect(lambda checked=False: webbrowser.open(self.links.get("telegram")))
                elif role == "repo":
                    act.triggered.connect(lambda checked=False: webbrowser.open(self.links.get("repo")))
                menu.addAction(act)
            self.addMenu(menu)
