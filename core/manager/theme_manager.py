from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt, Signal, QObject, QTimer
import platform
import subprocess
from PySide6.QtWidgets import QApplication

from core.enums.app_themes import AppTheme
from core.enums.log_level import LogLevel
from core.util.logger import Logger


def _check_system_theme_change():
    """Check if system theme has changed and update if in AUTO mode."""
    if ThemeManager.current_theme != AppTheme.AUTO:
        return

    current_system_theme = AppTheme.DARK if is_system_dark_mode() else AppTheme.LIGHT

    # If system theme changed, we're in AUTO mode, update the theme
    if current_system_theme != ThemeManager.last_system_theme:
        ThemeManager._last_system_theme = current_system_theme
        ThemeManager.set_theme(AppTheme.AUTO)


class ThemeManager(QObject):
    theme_changed = Signal(AppTheme)
    _instance = None
    _current_theme: AppTheme = AppTheme.AUTO
    _config: dict = {}
    _last_system_theme: AppTheme = None  # Track last detected system theme

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: dict = None):
        if getattr(self, "_initialized", False):
            return
        super().__init__()
        self._initialized = True
        ThemeManager._config = config or {}
        mode = ThemeManager._config.get("WINDOW_THEME_MODE", "AUTO").upper()
        try:
            ThemeManager._current_theme = AppTheme(mode) if not isinstance(mode, AppTheme) else mode
        except ValueError:
            Logger.error(f"Unmappable 'WINDOW_THEME_MODE' == '{mode}' in config.")
            Logger.debug("Falling back to LIGHT theme mode.")
            ThemeManager._current_theme = AppTheme.LIGHT

        # Detect initial system theme
        ThemeManager._last_system_theme = AppTheme.DARK if is_system_dark_mode() else AppTheme.LIGHT

        ThemeManager.apply_theme()

        # Set up periodic system theme checking for AUTO mode
        self._system_theme_timer = QTimer()
        self._system_theme_timer.timeout.connect(_check_system_theme_change)
        self._system_theme_timer.start(1000)  # Check every second

    # -----------------------
    # Theme Control
    # -----------------------
    @staticmethod
    def toggle_theme():
        """Switches between light and dark modes."""
        theme = ThemeManager._current_theme

        # If current theme is AUTO, toggle manually ignoring OS changes
        if theme == AppTheme.AUTO:
            # Use the current system theme as base for toggling
            current_effective_theme = ThemeManager._last_system_theme
            theme = AppTheme.DARK if current_effective_theme == AppTheme.LIGHT else AppTheme.LIGHT
        else:
            theme = AppTheme.LIGHT if theme == AppTheme.DARK else AppTheme.DARK

        ThemeManager.set_theme(theme)

    @staticmethod
    def set_theme(theme: AppTheme):
        """Sets the theme and updates the palette."""
        if theme != ThemeManager._current_theme or theme == AppTheme.AUTO:
            ThemeManager._current_theme = theme
            ThemeManager._config["WINDOW_THEME_MODE"] = theme.name

            # Update system theme reference when switching to AUTO
            if theme == AppTheme.AUTO:
                ThemeManager._last_system_theme = AppTheme.DARK if is_system_dark_mode() else AppTheme.LIGHT

            ThemeManager.apply_theme()
            # Emit signal through singleton instance
            if ThemeManager._instance:
                ThemeManager._instance.theme_changed.emit(theme)

    @staticmethod
    def apply_theme():
        """Applies the current theme to the QApplication."""
        theme = ThemeManager._current_theme

        # For AUTO mode, use the current system theme
        if theme == AppTheme.AUTO:
            theme = ThemeManager._last_system_theme

        app = QApplication.instance()
        if not app:
            Logger.error("QApplication instance not found. Cannot apply theme.")
            return

        if theme == AppTheme.DARK:
            ThemeManager._apply_dark_palette()
            Logger.debug("Applied DARK theme.")
        else:
            ThemeManager._apply_light_palette()
            Logger.debug("Applied LIGHT theme.")

        # Force UI refresh
        app.setStyle(app.style().objectName())

    # -----------------------
    # Palette Definitions
    # -----------------------
    @staticmethod
    def _apply_light_palette():
        app = QApplication.instance()
        if not app:
            Logger.error("QApplication instance not found. Cannot apply theme.")
            return

        light_palette = QPalette()
        light_palette.setColor(QPalette.Window, QColor(255, 255, 255))
        light_palette.setColor(QPalette.WindowText, Qt.black)
        light_palette.setColor(QPalette.Base, QColor(245, 245, 245))
        light_palette.setColor(QPalette.AlternateBase, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ToolTipBase, Qt.black)
        light_palette.setColor(QPalette.ToolTipText, Qt.white)
        light_palette.setColor(QPalette.Text, Qt.black)
        light_palette.setColor(QPalette.Button, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ButtonText, Qt.black)
        light_palette.setColor(QPalette.BrightText, Qt.red)
        light_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        light_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        light_palette.setColor(QPalette.HighlightedText, Qt.white)

        app.setPalette(light_palette)

    @staticmethod
    def _apply_dark_palette():
        app = QApplication.instance()
        if not app:
            Logger.error("QApplication instance not found. Cannot apply theme.")
            return

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

        app.setPalette(dark_palette)

    @staticmethod
    def get_current_theme() -> AppTheme:
        """Get the current theme (static)."""
        return ThemeManager._current_theme

    @staticmethod
    def get_effective_theme() -> AppTheme:
        """Get the effective theme (resolves AUTO to actual theme)."""
        if ThemeManager._current_theme == AppTheme.AUTO:
            return ThemeManager._last_system_theme
        return ThemeManager._current_theme

    @property
    def last_system_theme(self):
        return self._last_system_theme

    @property
    def current_theme(self):
        return self._current_theme


# -----------------------
# System Theme Detection (unchanged)
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
            is_theme_dark:bool = "Dark" in result.stdout
            Logger.debug(f"macOS theme detected: {'Dark' if is_theme_dark else 'Light'}")
            return is_theme_dark
        except Exception as e:
            Logger.warning(f"Failed to detect macOS theme: {e}, defaulting to light.")
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
            Logger.debug(f"Windows theme detected: {'Dark' if value == 0 else 'Light'}")
            return value == 0
        except Exception as e:
            Logger.warning(f"Failed to detect Windows theme: {e}, defaulting to light.")
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
                Logger.debug("Linux GTK theme detected: Dark")
                return True
        except Exception as e:
            Logger.debug(f"Failed to detect GTK theme: {e}, continuing to KDE check.")
            pass

        try:
            # Try KDE setting
            result = subprocess.run(
                ["kreadconfig5", "--group", "General", "--key", "ColorScheme"],
                capture_output=True, text=True
            )
            if "dark" in result.stdout.lower():
                Logger.debug("Linux KDE theme detected: Dark")
                return True
        except Exception as e:
            Logger.warning(f"Failed to detect KDE theme: {e}, defaulting to light.")
            pass

        Logger.debug("Linux theme defaulting to Light.")
        return False

    # --- Fallback (Qt heuristic) ---
    else:
        app = QApplication.instance()
        if app:
            palette = app.palette()
            window_color = palette.color(QPalette.Window)
            text_color = palette.color(QPalette.WindowText)
            return window_color.value() < text_color.value()
        return False