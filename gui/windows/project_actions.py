from __future__ import annotations

from pathlib import Path


def new_project(window):
    if window.document.is_dirty or window.current_project_path:
        action = window._confirm_new_project_action()
        if action is None:
            return
        if action == "save_current":
            if not window._save_project():
                return
            window._activate_new_project(window.session.__class__(), saved=True)
            return
        if action == "save_copy":
            if not window._save_project():
                return
            window._activate_new_project(
                window.template_catalog.build_unsaved_copy(window.session, window._current_project_dir()),
                saved=False,
            )
            return
        if action == "discard":
            window._activate_new_project(window.session.__class__(), saved=True)
            return

    window._activate_new_project(window.session.__class__(), saved=True)


def open_project(window, *, file_dialog_cls, message_box_cls, app_paths_cls):
    start_dir = window.current_project_path or str(app_paths_cls.documents_dir())
    path, _ = file_dialog_cls.getOpenFileName(
        window,
        window.localization.t("dialog.open_project.title"),
        start_dir,
        window.localization.t("dialog.project_files"),
    )
    if not path:
        return
    try:
        loaded_session = window.session_store.load(path)
        window.template_catalog.seed_default_template(loaded_session)
        selected_path = Path(path).expanduser().resolve()
        project_path = selected_path if selected_path.is_dir() else selected_path.parent
        window.document.load(loaded_session, project_path)
        window._apply_project_theme_mode(
            window.session.theme_mode,
            persist_to_session=True,
            save_last_session=False,
            sync_document_snapshot=True,
        )
        window._persist_last_session_async()
        window._refresh_pages()
        window.goto_stage(1)
    except Exception as exc:  # noqa: BLE001
        message_box_cls.critical(window, window.localization.t("dialog.open_project.failed_title"), str(exc))


def save_project(window):
    if window.current_project_path:
        return window._save_project_to_path(window.current_project_path)
    return window._save_project_as()


def save_project_as(window, *, file_dialog_cls, app_paths_cls):
    path = file_dialog_cls.getExistingDirectory(
        window,
        window.localization.t("dialog.save_project.title"),
        window.current_project_path or str(app_paths_cls.default_project_path()),
    )
    if not path:
        return False
    return window._save_project_to_path(path)


def save_project_to_path(window, path: str | Path):
    project_dir = Path(path).expanduser().resolve()
    session_to_save = window._prepare_session_for_save(project_dir)
    if session_to_save is None:
        return False

    saved_path = window.session_store.save(session_to_save, project_dir)
    loaded_session = window.session_store.load(Path(saved_path).parent)
    window.document.load(loaded_session, Path(saved_path).parent)
    window._persist_last_session_async()
    window._refresh_pages()
    return True


def activate_new_project(window, session, *, saved: bool):
    next_session = session.clone()
    window.template_catalog.seed_default_template(next_session)
    window.document.activate(next_session, None, saved=saved)
    window._apply_project_theme_mode(
        window.session.theme_mode,
        persist_to_session=True,
        save_last_session=False,
        sync_document_snapshot=saved,
    )
    window._persist_last_session_async()
    window._refresh_pages()
    window.goto_stage(1)


def confirm_new_project_action(window, *, message_box_cls):
    message_box = message_box_cls(window)
    message_box.setIcon(message_box_cls.Question)
    message_box.setWindowTitle(window.localization.t("dialog.new_project_confirm.title"))
    message_box.setText(window.localization.t("dialog.new_project_confirm.body"))
    save_current_button = message_box.addButton(
        window.localization.t("dialog.new_project_confirm.save_current"),
        message_box_cls.AcceptRole,
    )
    save_copy_button = message_box.addButton(
        window.localization.t("dialog.new_project_confirm.save_copy"),
        message_box_cls.ActionRole,
    )
    discard_button = message_box.addButton(
        window.localization.t("dialog.new_project_confirm.discard"),
        message_box_cls.DestructiveRole,
    )
    cancel_button = message_box.addButton(
        window.localization.t("dialog.new_project_confirm.cancel"),
        message_box_cls.RejectRole,
    )
    message_box.exec()

    clicked_button = message_box.clickedButton()
    if clicked_button is save_current_button:
        return "save_current"
    if clicked_button is save_copy_button:
        return "save_copy"
    if clicked_button is discard_button:
        return "discard"
    if clicked_button is cancel_button:
        return None
    return None


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
    target_session.template_path = window.session_store.resolve_effective_template_path(
        target_session,
        window._current_project_dir(),
    )


def refresh_template_toolbar(window):
    selected_type = window.session.selected_template_type
    type_names = [entry.name for entry in window.session.template_types]

    window.template_type_combo.blockSignals(True)
    window.template_combo.blockSignals(True)
    try:
        window.template_type_combo.clear()
        for type_name in type_names:
            window.template_type_combo.addItem(type_name, type_name)

        if selected_type:
            index = window.template_type_combo.findData(selected_type)
            if index >= 0:
                window.template_type_combo.setCurrentIndex(index)
        elif window.template_type_combo.count() > 0:
            window.template_type_combo.setCurrentIndex(0)

        current_type = window.session.selected_template_type
        template_entries = window.session.templates_for_type(current_type)
        window.template_combo.clear()
        for entry in template_entries:
            window.template_combo.addItem(entry.label, entry.id)

        if window.session.selected_template:
            index = window.template_combo.findData(window.session.selected_template)
            if index >= 0:
                window.template_combo.setCurrentIndex(index)
        elif window.template_combo.count() > 0:
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
    window.document.mark_unsaved()
    window._persist_last_session_async()
    window._refresh_pages()


def show_about(window, *, message_box_cls):
    message_box_cls.information(
        window,
        window.localization.t("dialog.about.title"),
        window.localization.t("dialog.about.body"),
    )
