from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from Configs.configs_file_manager import load_config
from UI.setup_ui import apply_app_metadata, center_on_screen, apply_window_metadata
from UI.main_window import MainWindow
from UI.splash_screen_window import show_splash
import sys

BASE_PATH = Path(__file__).resolve().parent


def main():
    app = QApplication(sys.argv)
    apply_app_metadata(app, base_path=BASE_PATH)

    cfg = load_config(BASE_PATH)
    splash_delay = cfg["splash"]["delay_ms"]

    splash = show_splash(BASE_PATH, delay_ms=splash_delay)
    
    splash.update_status("Initializing application...")
    app.processEvents()

    win = MainWindow(base_path=BASE_PATH)
    
    splash.update_status("Loading user interface...")
    app.processEvents()
    
    sidebar = apply_window_metadata(win, BASE_PATH)
    
    def on_scan_progress(status):
        splash.update_status(status)
        app.processEvents()
    
    sidebar.start_navigation_init(on_scan_progress)
    
    app.processEvents()

    def show_window():
        splash.close()
        win.show()
        center_on_screen(win)
    
    QTimer.singleShot(splash_delay, show_window)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
