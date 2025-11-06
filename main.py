import sys
from PySide6.QtWidgets import QApplication
from core.config.configuration import Config
from gui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    # 1️ Load configuration first
    config = Config.get()
    # 2️ Initialize the QApplication
    app = QApplication(sys.argv)
    # 4️ Create and show the main window
    window = MainWindow(config)
    window.show()
    # 5️ Start the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
