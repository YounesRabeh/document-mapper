from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, Signal, QObject
from core.enums.app_themes import AppTheme
import platform
import subprocess
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette
from PySide6.QtCore import Qt



class ThemeManager(QObject):
    """Singleton-style Theme Manager for handling light/dark/auto themes."""

    theme_changed = Signal(AppTheme)
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: dict = None):
        if getattr(self, "_initialized", False):
            return
        super().__init__()

        self._initialized = True
        self.config = config or {}
        theme_mode = self.config.get("THEME_MODE", "AUTO")

        if isinstance(theme_mode, AppTheme):
            self.current_theme = theme_mode
        else:
            self.current_theme = AppTheme(theme_mode)

        self.apply_theme()

    # -----------------------
    # Public API
    # -----------------------

    def apply_theme(self):
        """Applies the current theme to the QApplication."""
        theme = self.current_theme

        if theme == AppTheme.AUTO:
            theme = AppTheme.DARK if is_system_dark_mode() else AppTheme.LIGHT

        if theme == AppTheme.DARK:
            self._apply_dark_palette()
        else:
            self._apply_light_palette()

        # Emit signal for components that want to react (e.g., reload icons)
        self.theme_changed.emit(theme)

    def toggle_theme(self):
        """Switches between light and dark modes."""
        if self.current_theme == AppTheme.AUTO:
            # Toggle the *actual* system theme instead
            theme = AppTheme.DARK if not is_system_dark_mode() else AppTheme.LIGHT
        else:
            theme = AppTheme.LIGHT if self.current_theme == AppTheme.DARK else AppTheme.DARK

        self.set_theme(theme)

    def set_theme(self, theme: AppTheme):
        """Sets and applies a specific theme."""
        if theme != self.current_theme:
            self.current_theme = theme
            if self.config is not None:
                self.config["THEME_MODE"] = theme.name
            self.apply_theme()

    # -----------------------
    # Palette Definitions
    # -----------------------

    def _apply_light_palette(self):
        app = QApplication.instance()
        app.setPalette(QApplication.style().standardPalette())

    def _apply_dark_palette(self):
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ToolTipBase, Qt.white)
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)

        app = QApplication.instance()
        app.setPalette(dark_palette)

# -----------------------
# System Theme Detection
# -----------------------
def is_system_dark_mode() -> bool:
    """Detects whether the OS theme is dark or light across platforms."""
    system = platform.system()

    # --- macOS ---
    if system == "Darwin":
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True
            )
            return "Dark" in result.stdout
        except Exception:
            return False

    # --- Windows ---
    elif system == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            # 0 = dark, 1 = light
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return value == 0
        except Exception:
            return False

    # --- Linux (try GTK or KDE settings) ---
    elif system == "Linux":
        try:
            # Try GTK setting
            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True
            )
            if "dark" in result.stdout.lower():
                return True
        except Exception:
            pass

        try:
            # Try KDE setting
            result = subprocess.run(
                ["kreadconfig5", "--group", "General", "--key", "ColorScheme"],
                capture_output=True, text=True
            )
            if "dark" in result.stdout.lower():
                return True
        except Exception:
            pass

        return False

    # --- Fallback (Qt heuristic) ---
    else:
        app = QApplication.instance()
        palette = app.palette()
        window_color = palette.color(QPalette.Window)
        text_color = palette.color(QPalette.WindowText)
        return window_color.value() < text_color.value()