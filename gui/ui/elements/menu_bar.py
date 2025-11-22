from core.manager.theme_manager import ThemeManager

class MenuBar:
    """Centralized reusable menu bar definitions."""

    @staticmethod
    def default(stage):
        """
        :param stage: the stage QWidget that defines menu handlers.
        :returns: a default menu structure compatible with ``UIFactory.create_menu_bar``.
        ``stage`` is the QWidget (e.g. BaseStage subclass) that defines menu handlers.
        """
        return {
            "File": [
                ("New Project", None, None),
                ("Settings", None, None),
                (None, None),  # separator
                ("Exit", None, "Ctrl+Q"),
            ],
            "View": [
                ("Toggle Theme", ThemeManager.toggle_theme, "Ctrl+T"),
            ],
            "Help": [
                ("About", None, None),
            ]
        }