from __future__ import annotations

import re
from pathlib import Path
import shutil
import subprocess
import tempfile
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
    DOC_BACKEND_ERROR = (
        "Automatic .doc placeholder detection requires Spire.Doc or LibreOffice (soffice)."
    )

    def __init__(
        self,
        process_runner=None,
        soffice_resolver=None,
    ):
        self.process_runner = process_runner or subprocess.run
        self.soffice_resolver = soffice_resolver or shutil.which
        self._placeholder_cache: dict[
            tuple[str, str, str, str],
            tuple[tuple[int, int], list[str]],
        ] = {}

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

        backend_id = self._detect_backend(path)
        cache_key = (str(path), start, end, backend_id)
        signature = self._build_signature(path)
        cached = self._placeholder_cache.get(cache_key)
        if cached and cached[0] == signature:
            return list(cached[1])

        text = self._extract_template_text(path, backend_id)
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

    def _extract_template_text(self, path: Path, backend_id: str | None = None) -> str:
        selected_backend = backend_id or self._detect_backend(path)
        if selected_backend == "docx_xml":
            return self._extract_docx_text(path)
        if selected_backend == "doc:spire":
            return self._extract_doc_text_with_spire(path)
        if selected_backend.startswith("doc:soffice:"):
            soffice_path = selected_backend.split(":", 2)[2]
            return self._extract_doc_text_with_soffice(path, soffice_path)
        if selected_backend.startswith("doc:spire|soffice:"):
            soffice_path = selected_backend.split(":", 2)[2]
            try:
                return self._extract_doc_text_with_spire(path)
            except Exception:  # noqa: BLE001
                return self._extract_doc_text_with_soffice(path, soffice_path)
        raise RuntimeError(f"Unsupported template backend: {selected_backend}")

    def _detect_backend(self, path: Path) -> str:
        if zipfile.is_zipfile(path):
            return "docx_xml"

        if path.suffix.lower() == ".doc":
            soffice_path = self.soffice_resolver("soffice")
            if self._spire_is_available() and soffice_path:
                return f"doc:spire|soffice:{soffice_path}"
            if self._spire_is_available():
                return "doc:spire"
            if soffice_path:
                return f"doc:soffice:{soffice_path}"
            raise RuntimeError(self.DOC_BACKEND_ERROR)

        raise RuntimeError(f"Unsupported template format for placeholder detection: {path.suffix or path.name}")

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

    def _extract_doc_text_with_spire(self, path: Path) -> str:
        from spire.doc import Document

        document = Document()
        try:
            document.LoadFromFile(str(path))
            return str(document.GetText() or "")
        finally:
            close_method = getattr(document, "Close", None)
            if callable(close_method):
                close_method()

    def _extract_doc_text_with_soffice(self, path: Path, soffice_path: str) -> str:
        with tempfile.TemporaryDirectory(prefix="document-mapper-doc-") as temp_dir:
            output_dir = Path(temp_dir)
            self.process_runner(
                [
                    soffice_path,
                    "--headless",
                    "--nologo",
                    "--nodefault",
                    "--norestore",
                    "--nolockcheck",
                    "--invisible",
                    "--nofirststartwizard",
                    "--convert-to",
                    "txt:Text",
                    "--outdir",
                    str(output_dir),
                    str(path),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=30,
            )
            txt_candidates = sorted(output_dir.glob("*.txt"))
            if not txt_candidates:
                raise RuntimeError(f"LibreOffice did not produce a text export for {path.name}.")
            return txt_candidates[0].read_text(encoding="utf-8", errors="ignore")

    def _spire_is_available(self) -> bool:
        try:
            from spire.doc import Document  # noqa: F401
        except ImportError:
            return False
        return True

    def _build_signature(self, path: Path) -> tuple[int, int]:
        stat = path.stat()
        return stat.st_mtime_ns, stat.st_size
