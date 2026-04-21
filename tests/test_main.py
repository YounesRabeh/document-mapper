from __future__ import annotations

import threading

import main as main_module


class _FakeApp:
    def __init__(self, force_process_exit: bool = False):
        self._force_process_exit = force_process_exit

    def property(self, name: str):
        if name == main_module.MainWindow.FORCE_PROCESS_EXIT_PROPERTY:
            return self._force_process_exit
        return None


def test_has_live_non_daemon_threads_ignores_main_and_daemon_threads(monkeypatch):
    main_thread = threading.main_thread()

    class FakeThread:
        def __init__(self, *, alive: bool, daemon: bool):
            self._alive = alive
            self.daemon = daemon

        def is_alive(self) -> bool:
            return self._alive

    monkeypatch.setattr(
        main_module.threading,
        "enumerate",
        lambda: [main_thread, FakeThread(alive=True, daemon=True), FakeThread(alive=False, daemon=False)],
    )

    assert main_module._has_live_non_daemon_threads() is False


def test_has_live_non_daemon_threads_detects_background_worker(monkeypatch):
    main_thread = threading.main_thread()

    class FakeThread:
        daemon = False

        @staticmethod
        def is_alive() -> bool:
            return True

    monkeypatch.setattr(main_module.threading, "enumerate", lambda: [main_thread, FakeThread()])

    assert main_module._has_live_non_daemon_threads() is True


def test_should_force_process_exit_uses_app_property(monkeypatch):
    monkeypatch.setattr(main_module, "_has_live_non_daemon_threads", lambda: False)

    assert main_module._should_force_process_exit(_FakeApp(force_process_exit=True)) is True
    assert main_module._should_force_process_exit(_FakeApp(force_process_exit=False)) is False


def test_should_force_process_exit_uses_thread_fallback(monkeypatch):
    monkeypatch.setattr(main_module, "_has_live_non_daemon_threads", lambda: True)

    assert main_module._should_force_process_exit(_FakeApp(force_process_exit=False)) is True
