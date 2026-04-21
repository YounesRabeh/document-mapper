import os
import sys
import threading
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.config.configuration import Config
from core.util.app_icon import apply_app_icon_setup, configure_qt_application_identity
from gui.windows import MainWindow


def _has_live_non_daemon_threads() -> bool:
    """Return True when background Python threads would keep the process alive."""
    main_thread = threading.main_thread()
    for thread in threading.enumerate():
        if thread is main_thread:
            continue
        if thread.is_alive() and not thread.daemon:
            return True
    return False


def _should_force_process_exit(app: QApplication) -> bool:
    """Force process exit when shutdown left background work behind."""
    if bool(app.property(MainWindow.FORCE_PROCESS_EXIT_PROPERTY)):
        return True
    return _has_live_non_daemon_threads()


def main():
    """Main entry point for the application."""
    # 1️ Load configuration first
    config = Config.get()
    app_name = config.get("APP_NAME", "Document Mapper")
    organization_name = config.get("APP_ORGANIZATION", "Document Mapper")
    organization_domain = config.get("APP_DOMAIN", "")
    configure_qt_application_identity(
        app_name=app_name,
        organization_name=organization_name,
        organization_domain=organization_domain,
    )
    # 2️ Initialize the QApplication
    app = QApplication(sys.argv)
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
    exit_code = app.exec()
    if _should_force_process_exit(app):
        os._exit(int(exit_code))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
