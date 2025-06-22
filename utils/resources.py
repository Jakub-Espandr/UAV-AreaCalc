import os
import sys
from PySide6.QtGui import QIcon, QFontDatabase

def get_app_icon():
    """Gets the application icon QIcon object, preferring .icns on macOS."""
    try:
        # Correctly determine base_dir even when run from different locations
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if sys.platform == "darwin":
            icon_path = os.path.join(base_dir, 'assets', 'icons', 'icon.icns')
        else:
            icon_path = os.path.join(base_dir, 'assets', 'icons', 'icon.png')
            
        if os.path.exists(icon_path):
            return QIcon(icon_path)
    except Exception as e:
        print(f"Warning: Could not load application icon: {e}")
    return None

def load_custom_fonts():
    """Loads custom .ttf fonts from the assets/fonts directory."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        fonts_dir = os.path.join(base_dir, 'assets', 'fonts')
        if not os.path.exists(fonts_dir):
            print("Warning: Fonts directory not found.")
            return

        for font_file in os.listdir(fonts_dir):
            if font_file.lower().endswith('.ttf'):
                font_path = os.path.join(fonts_dir, font_file)
                QFontDatabase.addApplicationFont(font_path)
    except Exception as e:
        print(f"Warning: Could not load custom fonts: {e}") 