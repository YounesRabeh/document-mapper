from __future__ import annotations

from pathlib import Path

from core.mapping.models import (
    DEFAULT_IMPORTED_TEMPLATE_TYPE,
    ProjectSession,
    ProjectTemplateEntry,
    ProjectTemplateType,
    normalize_template_name,
)


class TemplateCatalogService:
    def infer_project_dir_from_session(self, session: ProjectSession) -> Path | None:
        selected_entry = session.selected_template_entry()
        if selected_entry is None or not selected_entry.is_managed or not selected_entry.relative_path:
            return None
        if not session.template_path:
            return None

        template_path = Path(session.template_path).expanduser().resolve()
        relative_parts = Path(selected_entry.relative_path).parts
        if not relative_parts or len(template_path.parts) <= len(relative_parts):
            return None

        if tuple(part.casefold() for part in template_path.parts[-len(relative_parts):]) != tuple(
            part.casefold() for part in relative_parts
        ):
            return None

        project_dir = template_path
        for _ in relative_parts:
            project_dir = project_dir.parent
        if not project_dir.exists():
            return None
        return project_dir.resolve()

    def normalize_template_selection(self, session: ProjectSession, project_dir: Path | None = None):
        session._ensure_template_catalog_consistency()

        available_type_names = {entry.name for entry in session.template_types}
        if session.selected_template_type and session.selected_template_type not in available_type_names:
            session.selected_template_type = ""

        if not session.selected_template_type and session.template_types:
            session.selected_template_type = session.template_types[0].name

        selected_entry = session.selected_template_entry()
        if selected_entry is not None and session.selected_template_type:
            if selected_entry.type_name != session.selected_template_type:
                session.selected_template = ""
                selected_entry = None

        available_templates = session.templates_for_type(session.selected_template_type)
        if session.selected_template and selected_entry is None:
            session.selected_template = ""

        if not session.selected_template and available_templates:
            session.selected_template = available_templates[0].id

        if session.selected_template and not session.selected_template_type:
            selected_entry = session.selected_template_entry()
            if selected_entry is not None:
                session.selected_template_type = selected_entry.type_name

        session.template_path = self.resolve_effective_template_path(session, project_dir)

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
            self.normalize_template_selection(session, project_dir)
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
        self.normalize_template_selection(session, project_dir)

    def resolve_effective_template_path(self, session: ProjectSession, project_dir: Path | None = None) -> str:
        if session.template_override_path:
            return str(Path(session.template_override_path).expanduser().resolve())

        selected_entry = session.selected_template_entry()
        if selected_entry is None:
            return ""

        if selected_entry.is_managed and selected_entry.relative_path and project_dir is not None:
            return str((project_dir / selected_entry.relative_path).resolve())
        if selected_entry.source_path:
            return str(Path(selected_entry.source_path).expanduser().resolve())
        return ""

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
