from __future__ import annotations

from pathlib import Path


def save_project(window, *, message_box_cls, app_paths_cls):
    return window._save_project_to_path(app_paths_cls.internal_project_dir(), message_box_cls=message_box_cls)


def save_project_to_path(window, path: str | Path, *, message_box_cls):
    project_dir = Path(path).expanduser().resolve()
    source_project_dir = window._current_project_dir()
    session_to_save = window._prepare_session_for_save(project_dir)
    if session_to_save is None:
        return False

    try:
        saved_path = window.session_store.save(
            session_to_save,
            project_dir,
            source_project_dir=source_project_dir,
        )
        loaded_session = window.session_store.load(project_dir)
        loaded_session.template_path = window.session_store.resolve_effective_template_path(
            loaded_session,
            project_dir,
        )
    except Exception as exc:  # noqa: BLE001
        message_box_cls.critical(
            window,
            window.localization.t("dialog.save_project.failed_title"),
            str(exc),
        )
        return False

    window.document.load(loaded_session, Path(saved_path).parent)
    window._persist_last_session_async()
    window._refresh_pages()
    return True

def prepare_session_for_save(window, project_dir: Path, *, message_box_cls):
    session_to_save = window.session.clone()
    if not session_to_save.template_override_path:
        window._sync_effective_template_path(session_to_save)
        return session_to_save

    override_path = Path(session_to_save.template_override_path).expanduser()
    if not override_path.exists():
        window._sync_effective_template_path(session_to_save)
        return session_to_save

    message_box = message_box_cls(window)
    message_box.setIcon(message_box_cls.Question)
    message_box.setWindowTitle(window.localization.t("dialog.template_override_save.title"))
    message_box.setText(
        window.localization.t(
            "dialog.template_override_save.body",
            path=override_path.name,
        )
    )
    store_button = message_box.addButton(
        window.localization.t("dialog.template_override_save.store"),
        message_box_cls.AcceptRole,
    )
    keep_button = message_box.addButton(
        window.localization.t("dialog.template_override_save.keep"),
        message_box_cls.DestructiveRole,
    )
    cancel_button = message_box.addButton(
        window.localization.t("dialog.template_override_save.cancel"),
        message_box_cls.RejectRole,
    )
    message_box.exec()

    clicked_button = message_box.clickedButton()
    if clicked_button is cancel_button:
        return None
    if clicked_button is store_button:
        window.template_catalog.store_template_override_in_project(session_to_save)

    window._sync_effective_template_path(session_to_save)
    return session_to_save


def current_project_dir(window):
    return window.document.project_dir


def sync_effective_template_path(window, session=None):
    target_session = session or window.session
    window.template_catalog.normalize_template_selection(
        target_session,
        window._current_project_dir(),
    )


def refresh_template_toolbar(window):
    selected_type = window.session.selected_template_type
    type_names = [entry.name for entry in window.session.template_types]
    none_label = window.localization.t("common.none")

    window.template_type_combo.blockSignals(True)
    window.template_combo.blockSignals(True)
    try:
        window.template_type_combo.clear()
        if type_names:
            for type_name in type_names:
                window.template_type_combo.addItem(type_name, type_name)

            index = window.template_type_combo.findData(selected_type)
            if index >= 0:
                window.template_type_combo.setCurrentIndex(index)
            elif window.template_type_combo.count() > 0:
                window.template_type_combo.setCurrentIndex(0)
        else:
            window.template_type_combo.addItem(none_label, "")
            window.template_type_combo.setCurrentIndex(0)

        current_type = window.session.selected_template_type
        template_entries = window.session.templates_for_type(current_type)
        window.template_combo.clear()
        if template_entries:
            for entry in template_entries:
                window.template_combo.addItem(entry.label, entry.id)

            index = window.template_combo.findData(window.session.selected_template)
            if index >= 0:
                window.template_combo.setCurrentIndex(index)
            elif window.template_combo.count() > 0:
                window.template_combo.setCurrentIndex(0)
        else:
            window.template_combo.addItem(none_label, "")
            window.template_combo.setCurrentIndex(0)

        has_types = bool(type_names)
        has_templates = bool(template_entries)
        window.template_type_combo.setEnabled(has_types)
        window.template_combo.setEnabled(has_templates)

        if window.session.template_override_path:
            window.template_toolbar_status.setText(
                window.localization.t(
                    "status.template_override_active",
                    name=Path(window.session.template_override_path).name,
                )
            )
        elif not has_types:
            window.template_toolbar_status.setText(window.localization.t("status.no_project_templates"))
        elif not has_templates:
            window.template_toolbar_status.setText(window.localization.t("status.no_templates_for_selected_type"))
        else:
            window.template_toolbar_status.setText(
                window.localization.t(
                    "status.active_template_ready",
                    name=window.session.active_template_name or window.localization.t("common.not_selected"),
                )
            )
    finally:
        window.template_type_combo.blockSignals(False)
        window.template_combo.blockSignals(False)


def handle_template_type_changed(window, _index: int):
    selected_type = str(window.template_type_combo.currentData() or "").strip()
    if selected_type == window.session.selected_template_type:
        return

    window.session.selected_template_type = selected_type
    template_entries = window.session.templates_for_type(selected_type)
    window.session.selected_template = template_entries[0].id if template_entries else ""
    window._persist_last_session()
    window.setup_page.refresh_from_session()
    window.mapping_page.bind_session(window.session)


def handle_template_selection_changed(window, _index: int):
    selected_template = str(window.template_combo.currentData() or "").strip()
    if selected_template == window.session.selected_template:
        return
    window.session.selected_template = selected_template
    window._persist_last_session()
    window.setup_page.refresh_from_session()
    window.mapping_page.bind_session(window.session)


def manage_templates(window, *, dialog_cls, accepted_code):
    dialog = dialog_cls(window.session, window.localization, window)
    if dialog.exec() != accepted_code:
        return

    window.session = dialog.edited_session()
    window._sync_effective_template_path()
    window._persist_last_session_async()
    window._refresh_pages()


def show_about(window, *, message_box_cls):
    version = str(window.config.get("APP_VERSION", "")).strip()
    author = str(window.config.get("APP_AUTHOR", "")).strip()

    details: list[str] = []
    if version:
        details.append(window.localization.t("dialog.about.version", value=version))
    if author:
        details.append(window.localization.t("dialog.about.author", value=author))

    body = window.localization.t("dialog.about.body")
    if details:
        body = f"{body}\n\n" + "\n".join(details)

    message_box_cls.information(
        window,
        window.localization.t("dialog.about.title"),
        body,
    )
