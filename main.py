import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.config.configuration import Config
from core.util.app_icon import apply_app_icon_setup
from gui.windows import MainWindow

def main():
    """Main entry point for the application."""
    # 1️ Load configuration first
    config = Config.get()
    # 2️ Initialize the QApplication
    app = QApplication(sys.argv)
    app_name = config.get("APP_NAME", "Document Mapper")
    app.setApplicationName(app_name)
    app.setOrganizationName(config.get("APP_ORGANIZATION", "Document Mapper"))
    app.setOrganizationDomain(config.get("APP_DOMAIN", ""))
    icon = apply_app_icon_setup(
        app,
        app_name=app_name,
        entrypoint_path=Path(__file__).resolve(),
    )

    # 4️ Create and show the main window
    window = MainWindow(config)
    if icon is not None:
        window.setWindowIcon(icon)
    window.showMaximized()
    # 5️ Start the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
