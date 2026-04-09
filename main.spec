from pathlib import Path
import ast

from PyInstaller.building.build_main import Analysis, EXE, PYZ
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

try:
    import tomllib
except ImportError:
    import tomli as tomllib


# --- Paths ---
_spec_path = globals().get("SPECPATH")
if _spec_path:
    project_root = Path(_spec_path).resolve()
else:
    project_root = Path.cwd().resolve()
icon_candidates = [
    project_root / "resources" / "icons" / "document-mapper.ico",
]
exe_icon = next((str(path) for path in icon_candidates if path.exists()), None)
if exe_icon:
    print(f"[INFO] Using app icon: {exe_icon}")
else:
    print("[WARN] App icon not found in resources/icons; build will use default icon.")

config_path = project_root / "config.toml"
if not config_path.exists():
    print("[WARN] config.toml not found in project root; build may miss env variables.")

# --- Load resources from config.toml ---
resources_cfg = {}
if config_path.exists():
    with open(config_path, "rb") as handle:
        cfg = tomllib.load(handle)
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

hiddenimports = [
    "spire.doc",
    "spire.doc.common",
    "openpyxl",
]

# --- Data files (config + gui + resources) ---
datas = [
    (str(project_root / "config.toml"), "."),
]

# Add ONLY the specific resource subfolders from config (not the base folder)
for key, path in resources_cfg.items():
    if key == "base":
        continue

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
    ["main.py"],
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

# --- Build one-file executable ---
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="document-mapper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=exe_icon,
)
