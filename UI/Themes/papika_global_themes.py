from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette


class PapikaTheme:
    
    @staticmethod
    def _is_dark_mode():
        app = QApplication.instance()
        if app:
            wc = app.palette().color(QPalette.Window)
            lum = 0.299 * wc.red() + 0.587 * wc.green() + 0.114 * wc.blue()
            return lum < 128
        return True
    
    @staticmethod
    def get_colors():
        is_dark = PapikaTheme._is_dark_mode()
        return {
            'primary': '#f7a128',
            'primary_hover': '#ff9500',
            'primary_rgba_light': 'rgba(247,161,40,0.06)',
            'primary_rgba_medium': 'rgba(247,161,40,0.15)',
            'secondary': '#16A34A',
            'secondary_hover': '#15803d',
            'danger': '#DC2626',
            'danger_hover': '#B91C1C',
            'icon_base': '#FFFFFF' if is_dark else '#000000',
            'icon_inactive': '#9CA3AF',
            'icon_active': '#f7a128',
            'text_primary': '#FFFFFF' if is_dark else '#000000',
            'text_secondary': '#9CA3AF',
            'text_danger': '#DC2626',
            'background_primary': '#1E1E1E' if is_dark else '#FFFFFF',
            'background_secondary': '#2D2D2D' if is_dark else '#F3F4F6',
            'border': '#3F3F3F' if is_dark else '#E5E7EB',
        }
    
    @staticmethod
    def get_sizes():
        return {
            'sidebar_width': 50,
            'sidebar_button_size': 40,
            'sidebar_min_width': 150,
            'button_height': 36,
            'control_height': 28,
            'progress_bar_height': 4,
            'header_height': 36,
            'grid_item_size': 150,
        }
    
    @staticmethod
    def get_spacing():
        return {
            'margin_small': 6,
            'margin_medium': 8,
            'margin_large': 10,
            'spacing_small': 5,
            'spacing_medium': 6,
            'spacing_large': 8,
            'padding_small': '6px',
            'padding_medium': '8px 12px',
            'padding_large': '10px 15px',
            'margins_none': (0, 0, 0, 0),
            'margins_small': (6, 6, 6, 6),
            'margins_medium': (8, 8, 8, 8),
            'margins_large': (10, 10, 10, 10),
            'margins_custom_1': (1, 1, 1, 1),
            'margins_custom_20': (20, 20, 20, 20),
        }
    
    @staticmethod
    def get_fonts():
        return {
            'size_small': '11px',
            'size_normal': '12px',
            'size_medium': '14px',
            'size_large': '16px',
            'weight_normal': 'normal',
            'weight_bold': 'bold',
        }
    
    @staticmethod
    def get_stylesheet_header(color_primary='#f7a128'):
        return f"font-weight: bold; padding: 8px 12px; color: {color_primary}; background-color: rgba(247,161,40,0.06);"
    
    @staticmethod
    def get_stylesheet_title():
        return "font-weight: bold;"
    
    @staticmethod
    def get_stylesheet_danger():
        colors = PapikaTheme.get_colors()
        return f"color: {colors['text_danger']}; font-weight: bold;"
    
    @staticmethod
    def apply_button_style(button, style='default'):
        colors = PapikaTheme.get_colors()
        sizes = PapikaTheme.get_sizes()
        button.setFixedHeight(sizes['button_height'])
        if style == 'primary':
            button.setStyleSheet(f"background-color: {colors['primary']}; color: white;")
        elif style == 'danger':
            button.setStyleSheet(f"background-color: {colors['danger']}; color: white;")
    
    @staticmethod
    def apply_sidebar_button_style(button):
        sizes = PapikaTheme.get_sizes()
        button.setFixedSize(sizes['sidebar_button_size'], sizes['sidebar_button_size'])
        button.setFlat(True)


PAPIKA_THEME = PapikaTheme()
