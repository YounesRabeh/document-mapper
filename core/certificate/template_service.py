from __future__ import annotations

import re
from pathlib import Path
import zipfile
from xml.etree import ElementTree

from core.certificate.models import DEFAULT_PLACEHOLDER_DELIMITER, derive_placeholder_boundaries


def _build_placeholder_pattern(delimiter: str) -> tuple[re.Pattern[str], str, str] | None:
    normalized = str(delimiter or "").strip()
    if not normalized:
        return None
    start, end = derive_placeholder_boundaries(normalized)
    prefix_guard = rf"(?<!{re.escape(start)})" if len(start) == 1 else ""
    suffix_guard = rf"(?!{re.escape(end)})" if len(end) == 1 else ""
    return re.compile(rf"{prefix_guard}{re.escape(start)}([^\r\n]+?){re.escape(end)}{suffix_guard}"), start, end


class TemplatePlaceholderService:
    def __init__(self):
        self._placeholder_cache: dict[tuple[str, str, str], tuple[tuple[int, int], list[str]]] = {}

    def extract_placeholders(
        self,
        template_path: str,
        delimiter: str = DEFAULT_PLACEHOLDER_DELIMITER,
    ) -> list[str]:
        if not template_path:
            return []

        pattern_result = _build_placeholder_pattern(delimiter)
        if pattern_result is None:
            return []
        pattern, start, end = pattern_result

        path = Path(template_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        cache_key = (str(path), start, end)
        signature = self._build_signature(path)
        cached = self._placeholder_cache.get(cache_key)
        if cached and cached[0] == signature:
            return list(cached[1])

        text = self._extract_template_text(path)
        placeholders: list[str] = []
        seen: set[str] = set()
        for match in pattern.finditer(text):
            inner_value = match.group(1).strip()
            if len(start) == 1 and inner_value.startswith(start):
                continue
            if len(end) == 1 and inner_value.endswith(end):
                continue
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
            keys_to_remove = [key for key in self._placeholder_cache if key[0] == cache_key]
            for key in keys_to_remove:
                self._placeholder_cache.pop(key, None)
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
