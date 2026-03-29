from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication, QWidget

from core.enums.app_themes import AppTheme
from core.util.system_info import *


class ThemeManager(QObject):
    """
    Manages application themes (light, dark, auto) and applies them to the QApplication.
    **Features:**

    - Singleton pattern to ensure a single theme manager instance.
    - Supports LIGHT, DARK, and AUTO themes.
    - AUTO theme detects system theme changes and updates accordingly.
    """
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

        ThemeManager._apply_current_theme()

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

        ThemeManager.set_canonical_theme(theme)

    @staticmethod
    def set_canonical_theme(theme: AppTheme):
        """
        Sets the canonical theme (LIGHT, DARK, AUTO).
        :param theme: The desired AppTheme to set.
        """
        if theme != ThemeManager._current_theme or theme == AppTheme.AUTO:
            ThemeManager._current_theme = theme
            ThemeManager._config["WINDOW_THEME_MODE"] = theme.name

            # Update system theme reference when switching to AUTO
            if theme == AppTheme.AUTO:
                ThemeManager._last_system_theme = AppTheme.DARK if is_system_dark_mode() else AppTheme.LIGHT

            ThemeManager._apply_current_theme()
            # Emit signal through singleton instance
            if ThemeManager._instance:
                ThemeManager._instance.theme_changed.emit(theme)

    @staticmethod
    def _apply_current_theme():
        """Applies the current theme to the QApplication."""
        theme = ThemeManager._current_theme

        # For AUTO mode, use the current system theme
        if theme == AppTheme.AUTO:
            theme = ThemeManager._last_system_theme

        app = QApplication.instance()
        if not app:
            Logger.error("QApplication instance not found. Cannot apply theme.")
            return

        # Use a consistent Qt style so custom palettes render more predictably
        # across platforms and widget types.
        app.setStyle("Fusion")

        if theme == AppTheme.DARK:
            ThemeManager._apply_dark_palette()
            Logger.debug("Applied DARK theme.")
        else:
            ThemeManager._apply_light_palette()
            Logger.debug("Applied LIGHT theme.")

        # Force UI refresh
        app.setStyle(app.style().objectName())

    @staticmethod
    def apply_theme_to_widget(widget: QWidget, path: str):
        """
        Apply a QSS file to a widget.

        :param widget: The QWidget to style
        :param path: Full path to the .qss file
        """
        if not os.path.exists(path):
            Logger.error(f"QSS file not found: {path}")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                qss = f.read()
                widget.setStyleSheet(qss)
                Logger.debug(f"Applied stylesheet from {path} to widget {widget.objectName()}")
        except Exception as e:
            Logger.error(f"Failed to apply stylesheet: {e}")

    # -----------------------
    # Palette Definitions
    # -----------------------
    @staticmethod
    def _build_palette(
        *,
        window: QColor,
        window_text: QColor,
        base: QColor,
        alternate_base: QColor,
        text: QColor,
        button: QColor,
        button_text: QColor,
        highlight: QColor,
        highlighted_text: QColor,
        mid: QColor,
        midlight: QColor,
        light: QColor,
        dark: QColor,
        shadow: QColor,
        link: QColor,
        placeholder: QColor,
        disabled_text: QColor,
    ) -> QPalette:
        palette = QPalette()

        palette.setColor(QPalette.Window, window)
        palette.setColor(QPalette.WindowText, window_text)
        palette.setColor(QPalette.Base, base)
        palette.setColor(QPalette.AlternateBase, alternate_base)
        palette.setColor(QPalette.ToolTipBase, base)
        palette.setColor(QPalette.ToolTipText, text)
        palette.setColor(QPalette.Text, text)
        palette.setColor(QPalette.Button, button)
        palette.setColor(QPalette.ButtonText, button_text)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, link)
        palette.setColor(QPalette.Highlight, highlight)
        palette.setColor(QPalette.HighlightedText, highlighted_text)
        palette.setColor(QPalette.PlaceholderText, placeholder)
        palette.setColor(QPalette.Mid, mid)
        palette.setColor(QPalette.Midlight, midlight)
        palette.setColor(QPalette.Light, light)
        palette.setColor(QPalette.Dark, dark)
        palette.setColor(QPalette.Shadow, shadow)

        for group in (QPalette.Disabled,):
            palette.setColor(group, QPalette.WindowText, disabled_text)
            palette.setColor(group, QPalette.Text, disabled_text)
            palette.setColor(group, QPalette.ButtonText, disabled_text)
            palette.setColor(group, QPalette.Highlight, mid)
            palette.setColor(group, QPalette.HighlightedText, highlighted_text)
            palette.setColor(group, QPalette.PlaceholderText, disabled_text)

        return palette

    @staticmethod
    def _apply_light_palette():
        app = QApplication.instance()
        if not app:
            Logger.error("QApplication instance not found. Cannot apply theme.")
            return

        light_palette = ThemeManager._build_palette(
            window=QColor("#edf2f7"),
            window_text=QColor("#1f2430"),
            base=QColor("#ffffff"),
            alternate_base=QColor("#dde5f0"),
            text=QColor("#1f2430"),
            button=QColor("#e7edf6"),
            button_text=QColor("#202531"),
            highlight=QColor("#3b82f6"),
            highlighted_text=QColor("#ffffff"),
            mid=QColor("#a7b2c2"),
            midlight=QColor("#c5cede"),
            light=QColor("#ffffff"),
            dark=QColor("#7e8898"),
            shadow=QColor("#5e6877"),
            link=QColor("#2563eb"),
            placeholder=QColor("#7f8898"),
            disabled_text=QColor("#96a0b0"),
        )

        app.setPalette(light_palette)

    @staticmethod
    def _apply_dark_palette():
        app = QApplication.instance()
        if not app:
            Logger.error("QApplication instance not found. Cannot apply theme.")
            return

        dark_palette = ThemeManager._build_palette(
            window=QColor("#272b31"),
            window_text=QColor("#f3f4f6"),
            base=QColor("#1d2025"),
            alternate_base=QColor("#323842"),
            text=QColor("#f3f4f6"),
            button=QColor("#39404b"),
            button_text=QColor("#f3f4f6"),
            highlight=QColor("#5b8cff"),
            highlighted_text=QColor("#ffffff"),
            mid=QColor("#5e6878"),
            midlight=QColor("#4b5360"),
            light=QColor("#798292"),
            dark=QColor("#171a1e"),
            shadow=QColor("#0f1215"),
            link=QColor("#7aa2ff"),
            placeholder=QColor("#8b95a3"),
            disabled_text=QColor("#757d8a"),
        )

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
# System Theme Detection
# -----------------------
def is_system_dark_mode() -> bool:
    if IS_MACOS:
        return detect_macos_theme()
    if IS_WINDOWS:
        return detect_windows_theme()
    if IS_LINUX:
        return detect_linux_theme()
    return _detect_fallback_theme()

def _detect_fallback_theme() -> bool:
    """Fallback theme detection using Qt heuristic."""
    app = QApplication.instance()
    if app:
        palette = app.palette()
        window_color = palette.color(QPalette.Window)
        text_color = palette.color(QPalette.WindowText)
        return window_color.value() < text_color.value()
    return False
