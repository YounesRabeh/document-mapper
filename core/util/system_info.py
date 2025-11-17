import os
import platform
import subprocess
from core.util.logger import Logger

def detect_os_name() -> str:
    """Detect the current operating system name."""
    return platform.system()

OS_NAME = detect_os_name()
IS_WINDOWS = OS_NAME == "Windows"
IS_LINUX = OS_NAME == "Linux"
IS_MACOS = OS_NAME == "Darwin"


def detect_macos_theme() -> bool:
    """Detect dark mode on macOS."""
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleInterfaceStyle"],
            capture_output=True, text=True
        )
        return "Dark" in result.stdout
    except Exception as e:
        Logger.warning(f"macOS theme detection failed: {e}")
        return False


def detect_windows_theme() -> bool:
    """Detect dark mode on Windows."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        )
        val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return val == 0
    except Exception as e:
        Logger.warning(f"Windows theme detection failed: {e}")
        return False


def detect_linux_theme() -> bool:
    """Detect dark theme from GTK/KDE."""
    if _detect_gtk_dark():
        return True
    if _detect_kde_dark():
        return True
    return False


def _detect_gtk_dark() -> bool:
    """Detect dark mode in GTK-based environments (like GNOME)."""
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True, text=True
        )
        return "dark" in result.stdout.lower()
    except:
        return False


def _detect_kde_dark() -> bool:
    """Detect dark mode in KDE Plasma."""
    try:
        result = subprocess.run(
            ["kreadconfig5", "--group", "General", "--key", "ColorScheme"],
            capture_output=True, text=True
        )
        return "dark" in result.stdout.lower()
    except:
        return False


# ============================================================
#  LibreOffice Integration
# ============================================================

def open_in_libreoffice(file_path: str) -> None:
    """Open a file in LibreOffice using OS-specific handlers."""
    # Check file existence first
    if not os.path.isfile(file_path):
        Logger.error(f"File does not exist: {file_path}")
        return

    try:
        if IS_LINUX:
            _open_libreoffice_linux(file_path)
        elif IS_WINDOWS:
            _open_libreoffice_windows(file_path)
        elif IS_MACOS:
            _open_libreoffice_macos(file_path)
        else:
            Logger.warning("Unsupported OS for LibreOffice.")
    except Exception as e:
        Logger.error(f"Failed to open file in LibreOffice: {e}")


def _open_libreoffice_linux(file_path: str) -> None:
    """Open a file in LibreOffice on Linux."""
    commands = [
        ["libreoffice", file_path],
        ["soffice", file_path]
    ]

    for cmd in commands:
        try:
            subprocess.Popen(cmd)
            Logger.info(f"Opened {file_path}")
            return
        except FileNotFoundError:
            continue

    Logger.warning("LibreOffice not found on Linux (libreoffice/soffice not in PATH).")


def _open_libreoffice_windows(file_path: str) -> None:
    """Open a file in LibreOffice on Windows."""
    possible_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
    ]

    for soffice in possible_paths:
        try:
            subprocess.Popen([soffice, file_path])
            Logger.info(f"Opened {file_path}")
            return
        except FileNotFoundError:
            continue

    Logger.warning("LibreOffice not found on Windows.")


def _open_libreoffice_macos(file_path: str) -> None:
    """Open a file in LibreOffice on macOS."""
    soffice = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    try:
        subprocess.Popen([soffice, file_path])
        Logger.info(f"Opened {file_path}")
    except FileNotFoundError:
        Logger.warning("LibreOffice not found on macOS.")