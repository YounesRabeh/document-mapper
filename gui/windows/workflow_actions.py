from __future__ import annotations

from core.util.logger import Logger


def refresh_pages(window):
    window._sync_effective_template_path()
    window._refresh_template_toolbar()
    window.setup_page.bind_session(window.session)
    window.mapping_page.bind_session(window.session)
    window.generate_page.bind_session(window.session)
    window.results_page.bind_result(window.last_result, window.session)
    window._refresh_workflow_state()


def persist_last_session(window):
    window._sync_effective_template_path()
    window._persist_last_session_async()
    window._refresh_template_toolbar()
    window.generate_page.bind_session(window.session)
    window.results_page.bind_result(window.last_result, window.session)
    window._refresh_workflow_state()


def goto_stage(window, index: int):
    if index < 1 or index > window.stage_manager.count():
        return False
    if not window._can_navigate_to_stage(index):
        window._refresh_workflow_state()
        return False
    target_index = index - 1
    if window.stage_manager.currentIndex() == target_index:
        window._handle_stage_changed(target_index)
        return True
    window.stage_manager.setCurrentIndex(target_index)
    return True


def handle_generation_result(window, result):
    window.last_result = result
    window.results_page.bind_result(result, window.session)
    window.goto_stage(4)


def retranslate_ui(window):
    window.setWindowTitle(window.localization.t("app.name"))
    window.sidebar_title.setText(window.localization.t("sidebar.heading"))
    window.sidebar_subtitle.setText(window.localization.t("sidebar.subtitle"))
    window.file_menu.setTitle(window.localization.t("menu.file"))
    window.view_menu.setTitle(window.localization.t("menu.view"))
    window.help_menu.setTitle(window.localization.t("menu.help"))
    window.language_menu.setTitle(window.localization.t("menu.language"))

    window.open_project_action.setText(window.localization.t("action.open_project"))
    window.save_project_action.setText(window.localization.t("action.save_project"))
    window.exit_action.setText(window.localization.t("action.exit"))
    window.toggle_theme_action.setText(window.localization.t("action.toggle_theme"))
    window.about_action.setText(window.localization.t("action.about"))
    window.template_type_label.setText(window.localization.t("field.template_type"))
    window.template_label.setText(window.localization.t("field.template"))
    window.manage_templates_button.setText(window.localization.t("button.manage_templates"))

    window.language_en_action.setText(window.localization.t("menu.language.en"))
    window.language_it_action.setText(window.localization.t("menu.language.it"))
    window.language_en_action.setChecked(window.localization.current_language == "en")
    window.language_it_action.setChecked(window.localization.current_language == "it")
    for card in window.stage_cards.values():
        card.retranslate()
    window._refresh_template_toolbar()
    window._refresh_workflow_state()


def handle_stage_changed(window, current_index: int):
    stage_number = current_index + 1
    if not window._can_navigate_to_stage(stage_number):
        fallback_stage = window._resolve_fallback_stage()
        if fallback_stage != stage_number:
            window.stage_manager.blockSignals(True)
            window.stage_manager.setCurrentIndex(fallback_stage - 1)
            window.stage_manager.blockSignals(False)
        window._handle_stage_changed(fallback_stage - 1)
        return

    window._last_valid_stage = stage_number
    if stage_number == 2:
        window.mapping_page.bind_session(window.session)
    elif stage_number == 3:
        window.generate_page.bind_session(window.session)
    elif stage_number == 4:
        window.results_page.bind_result(window.last_result, window.session)
    current_page = window.stage_manager.currentWidget()
    if hasattr(current_page, "scroll_to_top"):
        current_page.scroll_to_top()
    window._refresh_workflow_state()
    Logger.debug(f"Switched to workflow page {stage_number}")


def refresh_workflow_state(window):
    states = window.workflow_controller.compute_states(
        window.session,
        window.last_result,
        window.stage_manager.currentIndex() + 1,
        window.stage_manager.count(),
    )
    for index, card in window.stage_cards.items():
        card.set_stage_state(states[index])


def can_navigate_to_stage(window, index: int) -> bool:
    return window.workflow_controller.can_navigate_to_stage(
        index,
        window.session,
        window.last_result,
        window.stage_manager.currentIndex() + 1,
        window.stage_manager.count(),
    )


def resolve_fallback_stage(window) -> int:
    return window.workflow_controller.resolve_fallback_stage(
        window._last_valid_stage,
        window.session,
        window.last_result,
        window.stage_manager.currentIndex() + 1,
        window.stage_manager.count(),
    )
