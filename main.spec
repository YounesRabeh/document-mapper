# document_mapper.spec
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
import PySide6
import os

# --- Paths ---
project_root = Path(os.getcwd())

config_path = project_root / "config.toml"
if not config_path.exists():
    print("[WARN] .toml not found in project root; build may miss env variables.")

import ast

def detect_pyside_modules(source_dir: Path):
    """Detect PySide6 submodules actually imported in your project."""
    used = set()
    for py_file in source_dir.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("PySide6"):
                root = node.module.split(".")[1] if "." in node.module else None
                if root:
                    used.add(root)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("PySide6."):
                        root = alias.name.split(".")[1]
                        used.add(root)
    return sorted(used)

# --- Detect which PySide6 submodules are used ---
used_modules = detect_pyside_modules(project_root)
print(f"[INFO] Detected PySide6 modules: {used_modules}")

hiddenimports = []

# --- Data files (resources, gui, etc.) ---
datas = [
    (str(project_root / "config.toml"), "."),
    (str(project_root / "resources"), "resources"),
    (str(project_root / "gui"), "gui"),
]

# --- Include PySide6 dependencies (plugins, translations, etc.) ---
pyside6_base = Path(PySide6.__file__).parent
for mod in used_modules:
    datas += collect_data_files(f"PySide6.{mod}")
    hiddenimports += collect_submodules(f"PySide6.{mod}")

# --- Analysis phase ---
a = Analysis(
    ['main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

# --- Bundle Python code ---
pyz = PYZ(a.pure, a.zipped_data)

# --- Create the executable ---
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='document-mapper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # set to True if you want a console window for debugging
    onefile=True
)

# --- Collect everything into a single dist folder ---
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='document-mapper',
)
