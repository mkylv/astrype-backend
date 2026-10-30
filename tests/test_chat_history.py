"""GET /chat/history — Supabase mock'lu."""
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.api import routes_chat
from app.deps import CurrentUser, current_user
from app.main import app

USER_ID = "00000000-0000-0000-0000-000000000002"


class FakeQuery:
    def __init__(self, rows, calls):
        self.rows, self.calls = rows, calls

    def select(self, cols):
        self.calls.append(("select", cols))
        return self

    def eq(self, col, val):
        self.calls.append(("eq", col, val))
        return self

    def order(self, col, desc=False):
        self.calls.append(("order", col, desc))
        return self

    def limit(self, n):
        self.calls.append(("limit", n))
        return self

    def execute(self):
        return MagicMock(data=self.rows)


def _client(monkeypatch, rows, calls):
    sb = MagicMock()
    sb.table.side_effect = lambda name: FakeQuery(rows, calls) if name == "chat_messages" else None
    monkeypatch.setattr(routes_chat, "get_supabase", lambda: sb)
    app.dependency_overrides[current_user] = lambda: CurrentUser(id=USER_ID)
    return TestClient(app)


def test_history_oldest_first_and_scoped_to_user(monkeypatch):
    calls = []
    rows = [  # DB'den yeniden eskiye gelir
        {"role": "assistant", "content": "b", "created_at": "2026-10-30T10:01:00Z"},
        {"role": "user", "content": "a", "created_at": "2026-10-30T10:00:00Z"},
    ]
    try:
        res = _client(monkeypatch, rows, calls).get("/chat/history?limit=2")
    finally:
        app.dependency_overrides.pop(current_user, None)
    assert res.status_code == 200
    assert [m["content"] for m in res.json()["messages"]] == ["a", "b"]
    assert ("eq", "user_id", USER_ID) in calls
    assert ("limit", 2) in calls


def test_history_limit_validated(monkeypatch):
    try:
        res = _client(monkeypatch, [], []).get("/chat/history?limit=500")
    finally:
        app.dependency_overrides.pop(current_user, None)
    assert res.status_code == 422
