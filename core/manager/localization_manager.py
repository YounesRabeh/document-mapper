from __future__ import annotations

import json
import re
from pathlib import Path

from PySide6.QtCore import QObject, QSettings, Signal

from core.util.app_paths import AppPaths


def _load_translation_catalogs() -> dict[str, dict[str, str]]:
    """Load locale catalogs from disk and guarantee every supported language key exists."""
    locales_dir = AppPaths.locales_dir()
    if locales_dir is None:
        return {"en": {}, "it": {}, "es": {}, "fr": {}, "de": {}, "ru": {}}

    catalogs: dict[str, dict[str, str]] = {}
    for language in ("en", "it", "es", "fr", "de", "ru"):
        path = locales_dir / f"{language}.json"
        if not path.exists():
            catalogs[language] = {}
            continue
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        catalogs[language] = {str(key): str(value) for key, value in payload.items()}
    catalogs.setdefault("en", {})
    catalogs.setdefault("it", {})
    catalogs.setdefault("es", {})
    catalogs.setdefault("fr", {})
    catalogs.setdefault("de", {})
    catalogs.setdefault("ru", {})
    return catalogs


TRANSLATIONS = _load_translation_catalogs()


class LocalizationManager(QObject):
    """Provide translated UI/runtime strings and persist the selected language."""

    language_changed = Signal(str)
    supported_languages = ("en", "it", "es", "fr", "de", "ru")

    def __init__(self, config: dict | None = None):
        super().__init__()
        config = config or {}
        app_name = str(config.get("APP_NAME", "Document Mapper")).strip() or "Document Mapper"
        organization = str(config.get("APP_ORGANIZATION", "Document Mapper")).strip() or "Document Mapper"
        default_language = self._normalize_language(config.get("APP_LANGUAGE", "en"))

        self._settings = QSettings(organization, app_name)
        saved_language = self._normalize_language(self._settings.value("ui/language", default_language))
        self._language = saved_language or default_language

    @property
    def current_language(self) -> str:
        """Return the currently active language code."""
        return self._language

    def set_language(self, language: str):
        """Set and persist the active language, then notify listeners."""
        normalized = self._normalize_language(language)
        if normalized == self._language:
            return
        self._language = normalized
        self._settings.setValue("ui/language", normalized)
        self.language_changed.emit(normalized)

    def t(self, key: str, **kwargs) -> str:
        """Translate a key using the active catalog with English fallback."""
        translations = TRANSLATIONS.get(self._language, TRANSLATIONS["en"])
        value = translations.get(key, TRANSLATIONS["en"].get(key, key))
        if kwargs:
            return value.format(**kwargs)
        return value

    def translate_runtime_text(self, message: str) -> str:
        """Translate known runtime validation/error messages emitted by core services."""
        if self._language == "en" or not message:
            return message

        exact = {
            "Select an Excel workbook.": self.t("runtime.select_excel_workbook"),
            "Select a project template or set a template override.": self.t("runtime.select_word_template"),
            "Choose an output folder.": self.t("runtime.choose_output_folder"),
            "Set a placeholder delimiter before continuing.": self.t("runtime.placeholder_delimiter_required"),
            "Refresh and detect at least one placeholder before continuing.": self.t(
                "runtime.placeholder_detection_required"
            ),
            "Set an output naming schema before continuing.": self.t("runtime.output_naming_schema_required"),
            "Add at least one placeholder mapping.": self.t("runtime.add_placeholder_mapping"),
            "Spire.Doc is not installed. Install the runtime dependency before generating documents.": self.t(
                "runtime.spire_not_installed"
            ),
        }
        if message in exact:
            return exact[message]

        patterns = (
            (r"^Excel file not found: (?P<path>.+)$", "runtime.excel_file_not_found", "path"),
            (r"^Template file not found: (?P<path>.+)$", "runtime.template_file_not_found", "path"),
            (r"^Output folder is not writable: (?P<error>.+)$", "runtime.output_not_writable", "error"),
            (r"^License file not found: (?P<path>.+)$", "runtime.license_file_not_found", "path"),
            (r"^Cannot read Excel workbook: (?P<error>.+)$", "runtime.cannot_read_excel", "error"),
            (
                r"^Output naming schema token '(?P<token>.+)' is not available as a workbook column or built-in value\.$",
                "runtime.output_naming_schema_unknown_token",
                "token",
            ),
            (r"^Mapping row (?P<row>\d+) is missing a placeholder\.$", "runtime.mapping_missing_placeholder", "row"),
            (
                r"^Placeholder '(?P<placeholder>.+)' is mapped more than once\.$",
                "runtime.placeholder_duplicate",
                "placeholder",
            ),
            (r"^Mapping row (?P<row>\d+) is missing an Excel column\.$", "runtime.mapping_missing_column", "row"),
            (
                r"^Excel column '(?P<column>.+)' is not available in the selected workbook\.$",
                "runtime.column_not_available",
                "column",
            ),
            (r"^Failed to generate row (?P<row>\d+): (?P<error>.+)$", "runtime.failed_generate_row", None),
        )

        for pattern, key, primary_name in patterns:
            match = re.match(pattern, message)
            if not match:
                continue
            groups = match.groupdict()
            if primary_name is None:
                return self.t(key, **groups)
            return self.t(key, **groups)

        return message

    @staticmethod
    def _normalize_language(language: object) -> str:
        candidate = str(language or "").strip().lower()
        if candidate in TRANSLATIONS:
            return candidate
        return "en"
