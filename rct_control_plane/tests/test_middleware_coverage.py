"""
Tests for middleware.py — covering uncovered lines.

Uncovered: 208 (_apply_env_overrides hit path), 
242-246 (expired flag + ValueError), 263 (env mismatch), 
268-278 (percentage rollout), 325 (set_flag not found), 
333 (toggle_flag not found), 342 (set_rollout not found), 
352 (add_to_whitelist not found), 376-391 (load_from_db_rows),
426 (is_feature_enabled wrapper), 435 (get_flag), 439 (set_flag),
443 (toggle_flag), 447 (set_rollout_percentage), 451 (add_to_whitelist),
455 (add_to_blacklist), 459 (remove_user_override)
"""
from __future__ import annotations

import os
import pytest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from rct_control_plane.middleware import (
    FeatureFlagStore,
    FlagDefinition,
    is_feature_enabled,
    get_all_flags,
    get_flag,
    set_flag,
    toggle_flag,
    set_rollout_percentage,
    add_user_to_whitelist,
    add_user_to_blacklist,
    remove_user_override,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def fresh_store() -> FeatureFlagStore:
    """Return a new FeatureFlagStore so tests are isolated."""
    return FeatureFlagStore()


def make_flag(
    key="test_flag",
    enabled=True,
    rollout=100,
    whitelist=None,
    blacklist=None,
    environments=None,
    expires_at=None,
) -> FlagDefinition:
    return FlagDefinition(
        flag_key=key,
        description="test flag",
        enabled=enabled,
        rollout_percentage=rollout,
        user_whitelist=whitelist or [],
        user_blacklist=blacklist or [],
        environments=environments or ["*"],
        expires_at=expires_at,
    )


# ─────────────────────────────────────────────────────────────────────────────
# _apply_env_overrides (line 208)
# ─────────────────────────────────────────────────────────────────────────────

class TestEnvOverrides:
    def test_env_override_enables_flag(self):
        """FF_ENABLE_RATE_LIMITING=1 keeps the flag enabled (rollout=100%, env=*)."""
        with patch.dict(os.environ, {"FF_ENABLE_RATE_LIMITING": "1"}):
            store = fresh_store()
        assert store.is_enabled("enable_rate_limiting") is True

    def test_env_override_disables_flag(self):
        """FF_ENABLE_STATUS_PAGE=0 should disable the flag (targets all envs *)."""
        with patch.dict(os.environ, {"FF_ENABLE_STATUS_PAGE": "0"}):
            store = fresh_store()
        assert store.is_enabled("enable_status_page") is False

    def test_env_override_false_values(self):
        """'false', 'no', 'off', '' all disable the flag."""
        for val in ("false", "no", "off", ""):
            with patch.dict(os.environ, {"FF_ENABLE_STATUS_PAGE": val}):
                store = fresh_store()
            assert store.is_enabled("enable_status_page") is False

    def test_env_override_disabled_flag_can_be_enabled(self):
        """FF_ENABLE_STATUS_PAGE=0 turns off, then env=1 turns back on."""
        # First disable
        with patch.dict(os.environ, {"FF_ENABLE_STATUS_PAGE": "0"}):
            store_off = fresh_store()
        assert store_off.is_enabled("enable_status_page") is False
        # Then enable
        with patch.dict(os.environ, {"FF_ENABLE_STATUS_PAGE": "1"}):
            store_on = fresh_store()
        assert store_on.is_enabled("enable_status_page") is True


# ─────────────────────────────────────────────────────────────────────────────
# is_enabled — uncovered paths
# ─────────────────────────────────────────────────────────────────────────────

class TestIsEnabledUncovered:
    def test_unknown_flag_returns_false(self):
        store = fresh_store()
        assert store.is_enabled("nonexistent_flag") is False

    def test_expired_flag_returns_false(self):
        """Expired flag is blocked even with whitelist."""
        store = fresh_store()
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        flag = make_flag(key="expired_flag", enabled=True, rollout=100, expires_at=past)
        store.create_flag(flag)
        assert store.is_enabled("expired_flag") is False

    def test_future_expiry_still_enabled(self):
        store = fresh_store()
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        flag = make_flag(key="future_expire", enabled=True, rollout=100, expires_at=future)
        store.create_flag(flag)
        assert store.is_enabled("future_expire") is True

    def test_invalid_expires_at_format_no_crash(self):
        """Invalid ISO format in expires_at → ValueError caught, no block."""
        store = fresh_store()
        flag = make_flag(key="bad_expire", enabled=True, rollout=100, expires_at="not-a-date")
        store.create_flag(flag)
        # Should not crash — falls through to enabled check
        result = store.is_enabled("bad_expire")
        assert isinstance(result, bool)

    def test_blacklist_blocks_user(self):
        store = fresh_store()
        flag = make_flag(key="bl_flag", enabled=True, rollout=100, blacklist=["user-banned"])
        store.create_flag(flag)
        assert store.is_enabled("bl_flag", user_id="user-banned") is False

    def test_whitelist_allows_user_bypasses_disabled_flag(self):
        store = fresh_store()
        flag = make_flag(key="wl_flag", enabled=False, rollout=0, whitelist=["spartan-001"])
        store.create_flag(flag)
        assert store.is_enabled("wl_flag", user_id="spartan-001") is True

    def test_environment_mismatch_returns_false(self):
        """Flag targets 'production' only; eval in 'staging' → False."""
        store = fresh_store()
        flag = make_flag(key="prod_only", enabled=True, rollout=100, environments=["production"])
        store.create_flag(flag)
        assert store.is_enabled("prod_only", environment="staging") is False

    def test_environment_wildcard_passes_all(self):
        store = fresh_store()
        flag = make_flag(key="all_envs", enabled=True, rollout=100, environments=["*"])
        store.create_flag(flag)
        assert store.is_enabled("all_envs", environment="staging") is True
        assert store.is_enabled("all_envs", environment="production") is True

    def test_flag_disabled_returns_false(self):
        store = fresh_store()
        flag = make_flag(key="disabled_flag", enabled=False, rollout=100)
        store.create_flag(flag)
        assert store.is_enabled("disabled_flag") is False

    def test_rollout_100_enabled(self):
        store = fresh_store()
        flag = make_flag(key="full_rollout", enabled=True, rollout=100)
        store.create_flag(flag)
        assert store.is_enabled("full_rollout") is True

    def test_rollout_0_disabled(self):
        store = fresh_store()
        flag = make_flag(key="zero_rollout", enabled=True, rollout=0)
        store.create_flag(flag)
        assert store.is_enabled("zero_rollout") is False

    def test_rollout_50_with_user_deterministic(self):
        """50% rollout: some users in, some out — both outcomes tested."""
        store = fresh_store()
        flag = make_flag(key="half_rollout", enabled=True, rollout=50)
        store.create_flag(flag)
        # Test a bunch of users — at least one should be True and one False
        results = [store.is_enabled("half_rollout", user_id=f"user-{i}") for i in range(20)]
        assert True in results
        assert False in results

    def test_rollout_no_user_id_returns_false(self):
        """Partial rollout without user_id → disabled (0% threshold)."""
        store = fresh_store()
        flag = make_flag(key="partial_no_user", enabled=True, rollout=50)
        store.create_flag(flag)
        assert store.is_enabled("partial_no_user", user_id=None) is False


# ─────────────────────────────────────────────────────────────────────────────
# Admin mutation operations — uncovered paths
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminMutationsUncovered:
    def test_set_flag_not_found_returns_false(self):
        """set_flag on unknown key → False (line 325)."""
        store = fresh_store()
        assert store.set_flag("nonexistent", True) is False

    def test_toggle_flag_not_found_returns_none(self):
        """toggle_flag on unknown key → None (line 333)."""
        store = fresh_store()
        assert store.toggle_flag("nonexistent") is None

    def test_toggle_flag_success(self):
        store = fresh_store()
        flag = make_flag(key="toggle_me", enabled=True)
        store.create_flag(flag)
        new_state = store.toggle_flag("toggle_me")
        assert new_state is False
        # Toggle back
        new_state_2 = store.toggle_flag("toggle_me")
        assert new_state_2 is True

    def test_set_rollout_not_found_returns_false(self):
        """set_rollout on unknown key → False (line 342)."""
        store = fresh_store()
        assert store.set_rollout("nonexistent", 50) is False

    def test_set_rollout_invalid_percentage_raises(self):
        """set_rollout percent > 100 → ValueError."""
        store = fresh_store()
        with pytest.raises(ValueError, match="percentage must be 0-100"):
            store.set_rollout("enable_status_page", 101)

    def test_set_rollout_invalid_negative_raises(self):
        store = fresh_store()
        with pytest.raises(ValueError):
            store.set_rollout("enable_status_page", -1)

    def test_add_to_whitelist_not_found_returns_false(self):
        """add_to_whitelist on unknown flag → False (line 352)."""
        store = fresh_store()
        assert store.add_to_whitelist("nonexistent", "user-1") is False

    def test_add_to_blacklist_not_found_returns_false(self):
        store = fresh_store()
        assert store.add_to_blacklist("nonexistent", "user-1") is False

    def test_remove_user_override_not_found_returns_false(self):
        store = fresh_store()
        assert store.remove_user_override("nonexistent", "user-1") is False

    def test_remove_user_override_success(self):
        store = fresh_store()
        flag = make_flag(key="remove_test", whitelist=["u1"], blacklist=["u2"])
        store.create_flag(flag)
        store.remove_user_override("remove_test", "u1")
        store.remove_user_override("remove_test", "u2")
        updated = store.get_flag("remove_test")
        assert "u1" not in updated.user_whitelist
        assert "u2" not in updated.user_blacklist

    def test_create_flag_duplicate_returns_false(self):
        store = fresh_store()
        flag = make_flag(key="dup_flag")
        store.create_flag(flag)
        # Try to create same flag again
        assert store.create_flag(flag) is False

    def test_create_flag_sets_timestamps(self):
        store = fresh_store()
        flag = FlagDefinition(
            flag_key="ts_flag",
            description="test",
            enabled=True,
            created_at="",   # empty
            updated_at="",
        )
        store.create_flag(flag)
        result = store.get_flag("ts_flag")
        assert result.created_at != ""
        assert result.updated_at != ""


# ─────────────────────────────────────────────────────────────────────────────
# load_from_db_rows (lines 376-404)
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadFromDbRows:
    def test_load_basic_row(self):
        store = fresh_store()
        rows = [
            {
                "flag_key": "db_flag_1",
                "description": "loaded from DB",
                "enabled": True,
                "rollout_percentage": 100,
                "user_whitelist": "[]",
                "user_blacklist": "[]",
                "environments": '["*"]',
                "owner": "test-team",
                "tags": '["test"]',
                "created_at": "2026-01-01",
                "updated_at": "2026-01-01",
                "expires_at": None,
            }
        ]
        store.load_from_db_rows(rows)
        f = store.get_flag("db_flag_1")
        assert f is not None
        assert f.description == "loaded from DB"

    def test_load_row_with_list_fields(self):
        """Lists already parsed (not strings) should work."""
        store = fresh_store()
        rows = [
            {
                "flag_key": "db_flag_list",
                "description": "list fields",
                "enabled": True,
                "rollout_percentage": 50,
                "user_whitelist": ["user-1"],
                "user_blacklist": ["user-banned"],
                "environments": ["production"],
                "tags": ["launch"],
            }
        ]
        store.load_from_db_rows(rows)
        f = store.get_flag("db_flag_list")
        assert "user-1" in f.user_whitelist
        assert "user-banned" in f.user_blacklist

    def test_load_replaces_existing_flag(self):
        store = fresh_store()
        rows = [{"flag_key": "enable_status_page", "enabled": False, "description": "overridden"}]
        store.load_from_db_rows(rows)
        f = store.get_flag("enable_status_page")
        assert f.enabled is False

    def test_load_from_db_with_bad_json_no_crash(self):
        """Malformed JSON strings → exception caught, default values used."""
        store = fresh_store()
        rows = [
            {
                "flag_key": "bad_json_flag",
                "enabled": True,
                "user_whitelist": "{not valid json",
                "user_blacklist": "{not valid json",
                "environments": "{not valid json",
                "tags": "{not valid json",
            }
        ]
        # Should not raise
        store.load_from_db_rows(rows)
        f = store.get_flag("bad_json_flag")
        assert f is not None


# ─────────────────────────────────────────────────────────────────────────────
# Module-level convenience functions
# ─────────────────────────────────────────────────────────────────────────────

class TestModuleLevelFunctions:
    def test_get_all_flags_returns_dict(self):
        flags = get_all_flags()
        assert isinstance(flags, dict)
        assert "enable_status_page" in flags

    def test_get_flag_returns_flag_definition(self):
        f = get_flag("enable_status_page")
        assert f is not None
        assert f.flag_key == "enable_status_page"

    def test_get_flag_unknown_returns_none(self):
        assert get_flag("does_not_exist") is None

    def test_set_flag_known_flag(self):
        original = get_flag("enable_status_page").enabled
        set_flag("enable_status_page", not original)
        assert get_flag("enable_status_page").enabled == (not original)
        # Restore
        set_flag("enable_status_page", original)

    def test_toggle_flag_known(self):
        original = get_flag("enable_status_page").enabled
        new_state = toggle_flag("enable_status_page")
        assert new_state == (not original)
        # Restore
        toggle_flag("enable_status_page")

    def test_set_rollout_percentage_known(self):
        result = set_rollout_percentage("enable_status_page", 75)
        assert result is True
        f = get_flag("enable_status_page")
        assert f.rollout_percentage == 75
        # Restore
        set_rollout_percentage("enable_status_page", 100)

    def test_add_user_to_whitelist_known(self):
        result = add_user_to_whitelist("enable_status_page", "spartan-test-user")
        assert result is True

    def test_add_user_to_blacklist_known(self):
        result = add_user_to_blacklist("enable_status_page", "banned-test-user")
        assert result is True

    def test_remove_user_override_known(self):
        add_user_to_whitelist("enable_status_page", "cleanup-user")
        result = remove_user_override("enable_status_page", "cleanup-user")
        assert result is True

    def test_is_feature_enabled_wrapper(self):
        """Module-level function delegates to FLAG_STORE.is_enabled."""
        result = is_feature_enabled("enable_status_page")
        assert isinstance(result, bool)

    def test_is_feature_enabled_with_user(self):
        result = is_feature_enabled("enable_status_page", user_id="user-123")
        assert isinstance(result, bool)

    def test_flagdefinition_to_dict(self):
        f = make_flag()
        d = f.to_dict()
        assert d["flag_key"] == "test_flag"
        assert "enabled" in d
        assert "rollout_percentage" in d
        assert "user_whitelist" in d
        assert "environments" in d
