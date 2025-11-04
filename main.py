import sys
from PySide6.QtWidgets import QApplication
from core.config.configuration import Config
from gui.main_window import MainWindow


def main():
    """Main entry point for the application."""
    # 1️ Load configuration first
    config = Config.get()
    print("[CONFIG] Loaded successfully!")
    print(f"App Name: {config.get('APP_NAME')}")
    print(f"Window Size: {config.get('WINDOW_WIDTH')}x{config.get('WINDOW_HEIGHT')}")

    # 2️ Initialize the QApplication
    app = QApplication(sys.argv)

    # 3️ Apply optional theme or stylesheet if enabled
    if config.get("STYLE_SHEET_ENABLED", False):
        qss_path = config.get("QSS_THEME_PATH")
        if qss_path:
            try:
                with open(qss_path, "r", encoding="utf-8") as file:
                    app.setStyleSheet(file.read())
                print(f"[THEME] Loaded stylesheet from: {qss_path}")
            except FileNotFoundError:
                print(f"[WARNING] Stylesheet not found: {qss_path}")

    # 4️ Create and show the main window
    window = MainWindow(config)
    window.show()

    # 5️ Start the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
