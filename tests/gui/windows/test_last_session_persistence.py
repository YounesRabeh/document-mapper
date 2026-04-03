from __future__ import annotations

import tempfile
import threading
from pathlib import Path

from core.certificate.models import ProjectSession
from gui.windows.last_session_persistence import LastSessionPersistenceService


class BlockingSessionStore:
    def __init__(self):
        self.saved_sessions: list[ProjectSession] = []
        self.first_write_started = threading.Event()
        self.release_first_write = threading.Event()

    def save_last_session(self, session: ProjectSession):
        if not self.first_write_started.is_set():
            self.first_write_started.set()
            self.release_first_write.wait(timeout=1.0)
        self.saved_sessions.append(session.clone())
        return Path(tempfile.gettempdir()) / "last_session.json"


def test_last_session_persistence_service_coalesces_pending_snapshots():
    store = BlockingSessionStore()
    persistence = LastSessionPersistenceService(store)

    persistence.enqueue(ProjectSession(theme_mode="AUTO"))
    assert store.first_write_started.wait(timeout=1.0) is True

    persistence.enqueue(ProjectSession(theme_mode="DARK"))
    persistence.enqueue(ProjectSession(theme_mode="LIGHT"))
    store.release_first_write.set()

    assert persistence.flush_and_stop(timeout=1.0) is True
    assert [session.theme_mode for session in store.saved_sessions] == ["AUTO", "LIGHT"]
