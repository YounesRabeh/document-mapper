from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORMS_DIR = ROOT / "gui" / "forms"


def resolve_uic() -> str:
    """Return the available PySide6 UI compiler executable path."""
    for candidate in ("pyside6-uic", "pyside6-uic6"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise SystemExit(
        "Could not find 'pyside6-uic' in PATH. "
        "Install PySide6 and ensure its tools are available."
    )


def discover_ui_files(selected: list[str]) -> list[Path]:
    """Resolve requested .ui files or return all forms when no selection is provided."""
    all_files = sorted(FORMS_DIR.glob("*.ui"))
    if not selected:
        return all_files

    selected_set = {value.strip() for value in selected if value.strip()}
    matched: list[Path] = []
    missing: list[str] = []
    for value in selected_set:
        candidate = Path(value)
        if candidate.suffix != ".ui":
            candidate = candidate.with_suffix(".ui")
        if not candidate.is_absolute():
            candidate = FORMS_DIR / candidate.name
        if candidate.exists():
            matched.append(candidate)
        else:
            missing.append(value)

    if missing:
        raise SystemExit(f"Unknown .ui file(s): {', '.join(sorted(missing))}")
    return sorted(set(matched))


def output_path_for(ui_path: Path) -> Path:
    """Return generated Python output path for a .ui file."""
    return ui_path.with_name(f"ui_{ui_path.stem}.py")


def build_form(uic: str, ui_path: Path) -> Path:
    """Compile one .ui file into its `ui_*.py` companion module."""
    output_path = output_path_for(ui_path)
    subprocess.run(
        [uic, str(ui_path), "-o", str(output_path)],
        check=True,
        cwd=str(ROOT),
    )
    return output_path


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for selective UI form regeneration."""
    parser = argparse.ArgumentParser(
        description="Regenerate Python form classes from Qt Designer .ui files."
    )
    parser.add_argument(
        "forms",
        nargs="*",
        help="Optional .ui file names to rebuild, for example: main_window mapping_page",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entrypoint for rebuilding Qt Designer forms."""
    args = parse_args()
    uic = resolve_uic()
    ui_files = discover_ui_files(args.forms)

    if not ui_files:
        print("No .ui files found.")
        return 0

    print(f"Using {uic}")
    for ui_path in ui_files:
        output_path = build_form(uic, ui_path)
        print(f"Built {output_path.relative_to(ROOT)} from {ui_path.relative_to(ROOT)}")

    print(f"Generated {len(ui_files)} form module(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
