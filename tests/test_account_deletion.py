"""DELETE /account ve DELETE /memory — Supabase client mock'lu testler."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.api import routes_readings
from app.deps import CurrentUser, current_user
from app.main import app
from app.services import account

USER_ID = "00000000-0000-0000-0000-000000000001"


class FakeAuthError(Exception):
    def __init__(self, status: int, code: str) -> None:
        super().__init__(code)
        self.status = status
        self.code = code


class FakePgError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class FakeSupabase:
    """Silme zincirini kaydeder; tablo bazlı hata enjekte edilebilir."""

    def __init__(self, table_errors: dict[str, Exception] | None = None,
                 auth_error: Exception | None = None) -> None:
        self.table_errors = table_errors or {}
        self.deletes: list[tuple[str, str, str]] = []
        self.auth = MagicMock()
        if auth_error is not None:
            self.auth.admin.delete_user.side_effect = auth_error

    def table(self, name: str):
        fake = self

        class _Q:
            def delete(self):
                return self

            def eq(self, col, val):
                self._col, self._val = col, val
                return self

            def execute(self):
                if name in fake.table_errors:
                    raise fake.table_errors[name]
                fake.deletes.append((name, self._col, self._val))
                return MagicMock(data=[])

        return _Q()


@pytest.fixture
def client_with(monkeypatch):
    def _make(sb: FakeSupabase) -> TestClient:
        monkeypatch.setattr(routes_readings, "get_supabase", lambda: sb)
        app.dependency_overrides[current_user] = lambda: CurrentUser(id=USER_ID)
        return TestClient(app)

    yield _make
    app.dependency_overrides.pop(current_user, None)


def test_account_all_success(client_with):
    sb = FakeSupabase()
    res = client_with(sb).delete("/account")
    assert res.status_code == 200
    body = res.json()
    assert body["deleted"] is True
    assert body["auth_user_deleted"] is True
    tables = [t for t, _, _ in sb.deletes]
    # Her kullanıcı tablosu silinmeye çalışıldı, user_id ile.
    for t in account.ACCOUNT_USER_TABLES:
        assert (t, "user_id", USER_ID) in sb.deletes
    for t in ("wallets", "coin_transactions", "chat_usage", "subscriptions",
              "charts", "relationships", "daily_insight_cache"):
        assert t in tables
    # Profil veri tablolarından sonra, auth kullanıcısı en son.
    assert sb.deletes[-1] == ("profiles", "id", USER_ID)
    sb.auth.admin.delete_user.assert_called_once_with(USER_ID)


def test_account_auth_user_failure_returns_error(client_with):
    sb = FakeSupabase(auth_error=FakeAuthError(500, "unexpected_failure"))
    res = client_with(sb).delete("/account")
    assert res.status_code == 500
    assert res.json() == {"detail": {"code": "ACCOUNT_DELETE_FAILED", "step": "auth_user"}}


def test_account_already_deleted_user_is_success(client_with):
    sb = FakeSupabase(auth_error=FakeAuthError(404, "user_not_found"))
    res = client_with(sb).delete("/account")
    assert res.status_code == 200
    assert res.json()["deleted"] is True


def test_account_profile_failure_aborts_before_auth(client_with):
    sb = FakeSupabase(table_errors={"profiles": RuntimeError("boom")})
    res = client_with(sb).delete("/account")
    assert res.status_code == 500
    assert res.json()["detail"] == {"code": "ACCOUNT_DELETE_FAILED", "step": "profile"}
    assert "boom" not in res.text
    sb.auth.admin.delete_user.assert_not_called()


def test_account_table_failure_aborts(client_with):
    sb = FakeSupabase(table_errors={"wallets": RuntimeError("db down")})
    res = client_with(sb).delete("/account")
    assert res.status_code == 500
    assert res.json()["detail"]["step"] == "wallets"
    sb.auth.admin.delete_user.assert_not_called()


def test_account_missing_table_is_skipped(client_with):
    sb = FakeSupabase(table_errors={"chat_usage": FakePgError("PGRST205")})
    res = client_with(sb).delete("/account")
    assert res.status_code == 200
    sb.auth.admin.delete_user.assert_called_once()


def test_memory_all_keeps_chart_and_profile(client_with):
    sb = FakeSupabase()
    res = client_with(sb).delete("/memory")
    assert res.status_code == 200
    tables = {t for t, _, _ in sb.deletes}
    assert tables == {"chat_messages", "readings", "memory_chunks",
                      "relationships", "daily_insight_cache"}
    sb.auth.admin.delete_user.assert_not_called()


def test_memory_failure_returns_error(client_with):
    sb = FakeSupabase(table_errors={"readings": RuntimeError("x")})
    res = client_with(sb).delete("/memory")
    assert res.status_code == 500
    assert res.json()["detail"] == {"code": "MEMORY_DELETE_FAILED", "step": "readings"}
