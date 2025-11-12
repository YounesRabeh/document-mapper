from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
import PySide6
import os
import toml
import ast

# --- Paths ---
project_root = Path(os.getcwd())

config_path = project_root / "config.toml"
if not config_path.exists():
    print("[WARN] config.toml not found in project root; build may miss env variables.")

# --- Load resources from config.toml ---
resources_cfg = {}
if config_path.exists():
    cfg = toml.load(config_path)
    resources_cfg = cfg.get("resources", {})

# --- Detect PySide6 modules used ---
def detect_pyside_modules(source_dir: Path):
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

used_modules = detect_pyside_modules(project_root)
print(f"[INFO] Detected PySide6 modules: {used_modules}")

hiddenimports = []

# --- Data files (config + gui + resources) ---
datas = [
    (str(project_root / "config.toml"), "."),
    (str(project_root / "gui"), "gui"),
]

# Add ONLY the specific resource subfolders from config (not the base folder)
for key, path in resources_cfg.items():
    if key == "base":
        continue  # Skip base to avoid duplication

    abs_path = project_root / path
    if abs_path.exists() and abs_path.is_dir():
        print(f"[INFO] Including resource folder: {path}")
        for file_path in abs_path.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(project_root)
                datas.append((str(file_path), str(rel_path.parent)))

# --- Include PySide6 dependencies (plugins, translations, etc.) ---
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
    console=False,
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