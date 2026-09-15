"""RevenueCat abonelik yaşam döngüsü + zamana dayalı erişim kontrolü (ağsız, mock Supabase)."""
import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from app.db.supabase_client import get_user_tier, subscription_is_current
from app.services.subscription import revenuecat as rc

UID = "11111111-2222-3333-4444-555555555555"
UID2 = "66666666-7777-8888-9999-aaaaaaaaaaaa"
NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _ev(ev_type: str, **kw) -> dict:
    base = {
        "id": "evt-1",
        "type": ev_type,
        "app_user_id": UID,
        "entitlement_ids": ["premium"],
        "product_id": "monthly",
    }
    base.update(kw)
    return base


class FakeSB:
    """subscriptions tablosunu dict'te tutan minimal Supabase istemci taklidi."""

    def __init__(self, rows: dict | None = None):
        self.rows: dict[str, dict] = rows or {}
        self.rpc = MagicMock()

    def table(self, name):
        return _Query(self, name)


class _Query:
    def __init__(self, sb: FakeSB, name: str):
        self.sb, self.name = sb, name
        self.op, self.payload, self.filters = "select", None, {}

    def select(self, *_a, **_k):
        self.op = "select"
        return self

    def eq(self, col, val):
        self.filters[col] = val
        return self

    def limit(self, _n):
        return self

    def upsert(self, payload, on_conflict=None):
        self.op, self.payload = "upsert", payload
        return self

    def update(self, payload):
        self.op, self.payload = "update", payload
        return self

    def execute(self):
        res = MagicMock()
        if self.name != "subscriptions":
            res.data = []
            return res
        if self.op == "select":
            row = self.sb.rows.get(self.filters.get("user_id"))
            res.data = [dict(row)] if row else []
        elif self.op == "upsert":
            uid = self.payload["user_id"]
            self.sb.rows[uid] = {**self.sb.rows.get(uid, {}), **self.payload}
            res.data = [self.sb.rows[uid]]
        elif self.op == "update":
            uid = self.filters.get("user_id")
            if uid in self.sb.rows:
                self.sb.rows[uid].update(self.payload)
            res.data = []
        return res


def _run(sb, event):
    asyncio.run(rc.handle_event(sb, {"event": event}))


# ---- build_subscription_update (saf) ----
def test_cancellation_keeps_access_until_expiration():
    exp = NOW + timedelta(days=10)
    row = rc.build_subscription_update(_ev("CANCELLATION", expiration_at_ms=_ms(exp)), None, UID, now=NOW)
    assert row["is_active"] is True and row["tier"] == "premium"
    assert row["expires_at"] == exp.isoformat()
    assert subscription_is_current(row, now=NOW)
    assert not subscription_is_current(row, now=exp + timedelta(seconds=1))


def test_cancellation_refund_past_expiration_revokes():
    exp = NOW - timedelta(minutes=1)
    row = rc.build_subscription_update(_ev("CANCELLATION", expiration_at_ms=_ms(exp)), None, UID, now=NOW)
    assert row["is_active"] is False


def test_expiration_revokes():
    exp = NOW - timedelta(seconds=5)
    row = rc.build_subscription_update(_ev("EXPIRATION", expiration_at_ms=_ms(exp)), None, UID, now=NOW)
    assert row["is_active"] is False and row["tier"] == "free"


def test_stale_expiration_ignored_after_renewal():
    existing = {"is_active": True, "tier": "premium", "expires_at": (NOW + timedelta(days=30)).isoformat()}
    ev = _ev("EXPIRATION", expiration_at_ms=_ms(NOW - timedelta(days=1)))
    assert rc.build_subscription_update(ev, existing, UID, now=NOW) is None


def test_billing_issue_with_future_grace_extends():
    grace = NOW + timedelta(days=6)
    ev = _ev("BILLING_ISSUE", expiration_at_ms=_ms(NOW - timedelta(hours=1)),
             grace_period_expiration_at_ms=_ms(grace))
    row = rc.build_subscription_update(ev, None, UID, now=NOW)
    assert row["is_active"] is True and row["expires_at"] == grace.isoformat()


def test_billing_issue_without_grace_keeps_row():
    existing = {"is_active": True, "tier": "premium", "expires_at": (NOW + timedelta(days=1)).isoformat()}
    assert rc.build_subscription_update(_ev("BILLING_ISSUE"), existing, UID, now=NOW) is None
    past_grace = _ev("BILLING_ISSUE", grace_period_expiration_at_ms=_ms(NOW - timedelta(days=1)))
    assert rc.build_subscription_update(past_grace, existing, UID, now=NOW) is None


def test_reactivating_events_set_active_and_expiry():
    exp = NOW + timedelta(days=30)
    for t in ("INITIAL_PURCHASE", "RENEWAL", "UNCANCELLATION", "PRODUCT_CHANGE"):
        row = rc.build_subscription_update(_ev(t, expiration_at_ms=_ms(exp)), None, UID, now=NOW)
        assert row["is_active"] is True and row["tier"] == "premium", t
        assert row["expires_at"] == exp.isoformat()
        assert row["product_id"] == "monthly" and row["period"] == "monthly"


def test_product_change_uses_new_product_and_long_ids():
    ev = _ev("PRODUCT_CHANGE", product_id="astrype_sub_monthly", new_product_id="astrype_sub_yearly",
             expiration_at_ms=_ms(NOW + timedelta(days=3)))
    row = rc.build_subscription_update(ev, None, UID, now=NOW)
    assert row["product_id"] == "astrype_sub_yearly" and row["period"] == "yearly"


def test_coin_pack_does_not_touch_subscription():
    ev = _ev("NON_RENEWING_PURCHASE", product_id="astrype_coins_650", entitlement_ids=[])
    assert rc.build_subscription_update(ev, {"is_active": True, "tier": "premium"}, UID, now=NOW) is None


# ---- erişim kontrolü ----
def test_access_check_time_based():
    assert subscription_is_current({"is_active": True, "expires_at": None})  # lifetime
    assert subscription_is_current({"is_active": True, "expires_at": "2999-01-01T00:00:00+00:00"})
    assert not subscription_is_current({"is_active": True, "expires_at": "2000-01-01T00:00:00+00:00"})
    assert not subscription_is_current({"is_active": False, "expires_at": None})
    assert not subscription_is_current(None)
    assert subscription_is_current({"is_active": True, "expires_at": "2999-01-01T00:00:00.123456Z"})


def test_get_user_tier_past_expiry_is_free():
    sb = FakeSB({UID: {"user_id": UID, "tier": "premium", "is_active": True,
                       "expires_at": "2000-01-01T00:00:00+00:00"}})
    assert get_user_tier(sb, UID) == "free"
    sb.rows[UID]["expires_at"] = "2999-01-01T00:00:00+00:00"
    assert get_user_tier(sb, UID) == "premium"


# ---- handle_event (mock Supabase) ----
def test_handle_event_cancellation_then_expiration():
    sb = FakeSB()
    future = datetime.now(timezone.utc) + timedelta(days=5)
    _run(sb, _ev("INITIAL_PURCHASE", expiration_at_ms=_ms(future)))
    _run(sb, _ev("CANCELLATION", id="evt-2", expiration_at_ms=_ms(future)))
    assert get_user_tier(sb, UID) == "premium"
    _run(sb, _ev("EXPIRATION", id="evt-3", expiration_at_ms=_ms(future)))
    assert sb.rows[UID]["is_active"] is False
    assert get_user_tier(sb, UID) == "free"


def test_handle_event_anonymous_resolves_alias_uuid():
    sb = FakeSB()
    future = datetime.now(timezone.utc) + timedelta(days=5)
    _run(sb, _ev("INITIAL_PURCHASE", app_user_id="$RCAnonymousID:abc",
                 original_app_user_id="$RCAnonymousID:abc",
                 aliases=["$RCAnonymousID:abc", UID], expiration_at_ms=_ms(future)))
    assert get_user_tier(sb, UID) == "premium"


def test_handle_event_anonymous_without_uuid_skips():
    sb = FakeSB()
    _run(sb, _ev("INITIAL_PURCHASE", app_user_id="$RCAnonymousID:abc", aliases=[]))
    assert sb.rows == {}
    sb.rpc.assert_not_called()


def test_handle_event_transfer_moves_row():
    future = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    sb = FakeSB({UID: {"user_id": UID, "tier": "premium", "is_active": True,
                       "expires_at": future, "product_id": "monthly", "period": "monthly"}})
    _run(sb, {"type": "TRANSFER", "id": "evt-t",
              "transferred_from": [UID, "$RCAnonymousID:x"], "transferred_to": [UID2]})
    assert get_user_tier(sb, UID2) == "premium"
    assert get_user_tier(sb, UID) == "free"
    assert sb.rows[UID2]["expires_at"] == future


def test_subscription_coin_grant_unchanged():
    sb = FakeSB()
    future = datetime.now(timezone.utc) + timedelta(days=5)
    _run(sb, _ev("RENEWAL", id="evt-r", expiration_at_ms=_ms(future)))
    args = sb.rpc.call_args_list
    assert any(a.args[0] == "grant_coins" and a.args[1]["p_idempotency_key"] == "rc_sub:evt-r"
               and a.args[1]["p_amount"] == 700 for a in args)
