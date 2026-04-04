from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.certificate.models import (
    DEFAULT_IMPORTED_TEMPLATE_NAME,
    DEFAULT_IMPORTED_TEMPLATE_TYPE,
    ProjectSession,
    ProjectTemplateEntry,
    ProjectTemplateType,
    normalize_template_name,
)


class TemplateCatalogService:
    def __init__(self, default_template_path_provider: Callable[[], Path | None]):
        self._default_template_path_provider = default_template_path_provider

    def prune_unavailable_templates(self, session: ProjectSession, project_dir: Path | None = None):
        kept_entries: list[ProjectTemplateEntry] = []

        for entry in session.templates:
            candidate_path: Path | None = None
            if entry.is_managed and entry.relative_path and project_dir is not None:
                candidate_path = (project_dir / entry.relative_path).expanduser().resolve()
            elif entry.source_path:
                candidate_path = Path(entry.source_path).expanduser().resolve()
            elif session.selected_template == entry.id and session.template_path:
                candidate_path = Path(session.template_path).expanduser().resolve()

            if candidate_path is None or candidate_path.exists():
                kept_entries.append(entry)

        if len(kept_entries) == len(session.templates):
            return

        session.templates = kept_entries
        session.template_types = [
            template_type
            for template_type in session.template_types
            if any(entry.type_name == template_type.name for entry in session.templates)
        ]
        if session.selected_template and session.selected_template_entry() is None:
            session.selected_template = ""
        if session.selected_template_type and not session.templates_for_type(session.selected_template_type):
            session.selected_template_type = ""
        if not session.templates:
            session.template_path = ""
        session._ensure_template_catalog_consistency()

    def seed_default_template(self, session: ProjectSession):
        if session.templates:
            return

        default_template_path = self._default_template_path_provider()
        if default_template_path is None:
            return

        default_type = ProjectTemplateType(DEFAULT_IMPORTED_TEMPLATE_TYPE)
        default_entry = ProjectTemplateEntry(
            display_name=DEFAULT_IMPORTED_TEMPLATE_NAME,
            type_name=default_type.name,
            source_path=str(default_template_path),
            is_managed=False,
        )
        session.template_types = [default_type]
        session.templates = [default_entry]
        session.selected_template_type = default_type.name
        session.selected_template = default_entry.id
        session.template_path = str(default_template_path)

    def has_non_default_template_catalog(self, session: ProjectSession) -> bool:
        default_template_path = self._default_template_path_provider()
        if len(session.template_types) != 1 or len(session.templates) != 1:
            return bool(session.template_types or session.templates)

        template_type = session.template_types[0]
        template_entry = session.templates[0]
        if template_type.name != DEFAULT_IMPORTED_TEMPLATE_TYPE:
            return True
        if template_entry.label != DEFAULT_IMPORTED_TEMPLATE_NAME:
            return True
        if default_template_path is None:
            return True
        try:
            entry_path = Path(template_entry.source_path).expanduser().resolve() if template_entry.source_path else None
        except OSError:
            return True
        return entry_path != default_template_path.resolve()

    def build_unsaved_copy(self, session: ProjectSession, project_dir: Path | None) -> ProjectSession:
        copied_session = session.clone()
        if project_dir is not None:
            for entry in copied_session.templates:
                if entry.is_managed and entry.relative_path:
                    managed_path = (project_dir / entry.relative_path).resolve()
                    if managed_path.exists():
                        entry.source_path = str(managed_path)
                    entry.relative_path = ""
                    entry.is_managed = False
        copied_session.template_path = ""
        return copied_session

    def store_template_override_in_project(self, session: ProjectSession):
        if not session.template_override_path:
            return

        override_path = Path(session.template_override_path).expanduser().resolve()
        if not override_path.exists():
            return

        type_name = session.selected_template_type or DEFAULT_IMPORTED_TEMPLATE_TYPE
        if type_name not in {entry.name for entry in session.template_types}:
            session.template_types.append(ProjectTemplateType(type_name))

        display_name = self.unique_template_display_name(
            session,
            type_name,
            normalize_template_name(override_path.stem) or normalize_template_name(override_path.name),
        )
        new_entry = ProjectTemplateEntry(
            display_name=display_name,
            type_name=type_name,
            source_path=str(override_path),
            is_managed=False,
        )
        session.templates.append(new_entry)
        session.selected_template_type = type_name
        session.selected_template = new_entry.id
        session.template_override_path = ""
        session._ensure_template_catalog_consistency()

    def unique_template_display_name(
        self,
        session: ProjectSession,
        type_name: str,
        base_name: str,
        exclude_template_id: str = "",
    ) -> str:
        normalized = normalize_template_name(base_name) or "Template"
        existing = {
            entry.label.casefold()
            for entry in session.templates_for_type(type_name)
            if entry.id != exclude_template_id
        }
        candidate = normalized
        counter = 2
        while candidate.casefold() in existing:
            candidate = f"{normalized} {counter}"
            counter += 1
        return candidate
