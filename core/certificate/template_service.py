from __future__ import annotations

import re
from pathlib import Path
import zipfile
from xml.etree import ElementTree


PLACEHOLDER_PATTERN = re.compile(r"<<[^<>\r\n]+>>|<[^<>\r\n]+>")


class TemplatePlaceholderService:
    def __init__(self):
        self._placeholder_cache: dict[str, tuple[tuple[int, int], list[str]]] = {}

    def extract_placeholders(self, template_path: str) -> list[str]:
        if not template_path:
            return []

        path = Path(template_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        cache_key = str(path)
        signature = self._build_signature(path)
        cached = self._placeholder_cache.get(cache_key)
        if cached and cached[0] == signature:
            return list(cached[1])

        text = self._extract_template_text(path)
        placeholders: list[str] = []
        seen: set[str] = set()
        for match in PLACEHOLDER_PATTERN.finditer(text):
            placeholder = match.group(0).strip()
            if placeholder and placeholder not in seen:
                placeholders.append(placeholder)
                seen.add(placeholder)
        self._placeholder_cache[cache_key] = (signature, list(placeholders))
        return placeholders

    def clear_cache(self, template_path: str | None = None):
        if template_path:
            try:
                cache_key = str(Path(template_path).expanduser().resolve())
            except OSError:
                return
            self._placeholder_cache.pop(cache_key, None)
            return
        self._placeholder_cache.clear()

    def _extract_template_text(self, path: Path) -> str:
        if zipfile.is_zipfile(path):
            return self._extract_docx_text(path)
        return self._extract_binary_text(path)

    def _extract_docx_text(self, path: Path) -> str:
        chunks: list[str] = []
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if not name.startswith("word/") or not name.endswith(".xml"):
                    continue
                xml_bytes = archive.read(name)
                try:
                    root = ElementTree.fromstring(xml_bytes)
                except ElementTree.ParseError:
                    continue
                text_parts = [node.text for node in root.iter() if node.tag.endswith("}t") and node.text]
                if text_parts:
                    chunks.append("".join(text_parts))
        return "\n".join(chunks)

    def _extract_binary_text(self, path: Path) -> str:
        raw_bytes = path.read_bytes()
        for encoding in ("utf-8", "latin-1"):
            try:
                return raw_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw_bytes.decode("utf-8", errors="ignore")

    def _build_signature(self, path: Path) -> tuple[int, int]:
        stat = path.stat()
        return stat.st_mtime_ns, stat.st_size
