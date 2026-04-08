from __future__ import annotations

import threading
import time

from core.mapping.models import ProjectSession


class LastSessionPersistenceService:
    """Serialize last-session writes off the UI thread with explicit shutdown flushing."""

    def __init__(self, session_store):
        self._session_store = session_store
        self._condition = threading.Condition()
        self._pending_snapshot: ProjectSession | None = None
        self._latest_snapshot: ProjectSession | None = None
        self._worker: threading.Thread | None = None
        self._writing = False
        self._stop_requested = False
        self._last_error: Exception | None = None

    def enqueue(self, snapshot: ProjectSession):
        cloned = snapshot.clone()
        with self._condition:
            if self._stop_requested:
                return
            self._pending_snapshot = cloned
            self._latest_snapshot = cloned.clone()
            self._last_error = None
            self._ensure_worker_locked()
            self._condition.notify_all()

    def latest_snapshot(self) -> ProjectSession | None:
        with self._condition:
            if self._pending_snapshot is not None:
                return self._pending_snapshot.clone()
            if self._latest_snapshot is not None:
                return self._latest_snapshot.clone()
            return None

    def flush(self, timeout: float | None = None) -> bool:
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._condition:
            while self._pending_snapshot is not None or self._writing:
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    return False
                self._condition.wait(remaining)
            return self._last_error is None

    def flush_and_stop(self, timeout: float | None = None) -> bool:
        deadline = None if timeout is None else time.monotonic() + timeout
        with self._condition:
            self._stop_requested = True
            worker = self._worker
            self._condition.notify_all()

        flush_timeout = None if deadline is None else max(0.0, deadline - time.monotonic())
        flushed = self.flush(flush_timeout)

        if worker is None:
            return flushed

        join_timeout = None if deadline is None else max(0.0, deadline - time.monotonic())
        worker.join(join_timeout)
        return flushed and not worker.is_alive()

    def _ensure_worker_locked(self):
        worker = self._worker
        if worker is not None and worker.is_alive():
            return
        self._worker = threading.Thread(
            target=self._run,
            name="last-session-persist",
            daemon=False,
        )
        self._worker.start()

    def _run(self):
        while True:
            with self._condition:
                while self._pending_snapshot is None and not self._stop_requested:
                    self._condition.wait()
                if self._pending_snapshot is None and self._stop_requested:
                    return
                snapshot = self._pending_snapshot
                self._pending_snapshot = None
                self._writing = True

            error: Exception | None = None
            try:
                self._session_store.save_last_session(snapshot)
            except Exception as exc:  # noqa: BLE001
                error = exc
            with self._condition:
                self._writing = False
                self._last_error = error
                should_stop = self._pending_snapshot is None and self._stop_requested
                self._condition.notify_all()
            if should_stop:
                return
