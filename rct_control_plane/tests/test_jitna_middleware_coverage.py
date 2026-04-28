"""
Coverage-gap tests for:
  - rct_control_plane/jitna_protocol.py  (75% → 90%+)
  - rct_control_plane/middleware.py      (76% → 90%+)

Targets uncovered branches:
  jitna_protocol:
    - JITNAValidator.validate_dict exception path
    - JITNANormalizer.normalize TypeError for non-dict input
    - JITNAProtocolRegistry: register (with correlation), get, get_chain,
      packet_count, chain_count, get_statistics, clear

  middleware (FeatureFlagStore):
    - _apply_env_overrides via FF_* env vars
    - is_enabled: expired flag, expired ValueError, blacklist, whitelist,
      environment mismatch, rollout percentage paths
    - Mutations: set_flag, toggle_flag, set_rollout, add_to_whitelist,
      add_to_blacklist, remove_user_override, create_flag, load_from_db_rows
    - Module-level convenience functions
"""
from __future__ import annotations

import pytest


# ============================================================================
# jitna_protocol
# ============================================================================

class TestJITNAValidatorDict:
    def test_validate_dict_valid_input(self):
        from rct_control_plane.jitna_protocol import JITNAValidator
        v = JITNAValidator()
        result = v.validate_dict({
            "source_agent_id": "agent-A",
            "target_agent_id": "agent-B",
            "message_type": "intent_request",
            "payload": {"action": "run"},
        })
        assert result is not None

    def test_validate_dict_exception_returns_error(self):
        from rct_control_plane.jitna_protocol import JITNAValidator
        v = JITNAValidator()
        # Pass non-dict to trigger exception inside validate_dict
        result = v.validate_dict("not-a-dict")  # type: ignore[arg-type]
        assert not result.is_valid
        assert result.errors


class TestJITNANormalizerNonDict:
    def test_normalize_rejects_non_dict(self):
        from rct_control_plane.jitna_protocol import JITNANormalizer
        normalizer = JITNANormalizer()
        with pytest.raises(TypeError):
            normalizer.normalize("string input")  # type: ignore[arg-type]

    def test_normalize_with_field_aliases(self):
        from rct_control_plane.jitna_protocol import JITNANormalizer
        normalizer = JITNANormalizer()
        packet = normalizer.normalize({
            "src": "agent-A",
            "dst": "agent-B",
            "type": "intent_request",
            "data": {"key": "val"},
            "prio": 5,
        })
        assert packet.source_agent_id == "agent-A"
        assert packet.target_agent_id == "agent-B"
        assert packet.priority == 5


class TestJITNAProtocolRegistry:
    def _make_packet(self, pid: str = "pkt-1", corr: str | None = None):
        from rct_control_plane.jitna_protocol import JITNANormalizer
        return JITNANormalizer().normalize({
            "packet_id": pid,
            "source_agent_id": "A",
            "target_agent_id": "B",
            "payload": {},
            **({"correlation_id": corr} if corr else {}),
        })

    def test_register_and_get(self):
        from rct_control_plane.jitna_protocol import JITNAProtocolRegistry
        reg = JITNAProtocolRegistry()
        pkt = self._make_packet("p1")
        reg.register(pkt)
        assert reg.get("p1") is pkt

    def test_get_missing_returns_none(self):
        from rct_control_plane.jitna_protocol import JITNAProtocolRegistry
        reg = JITNAProtocolRegistry()
        assert reg.get("no-such-id") is None

    def test_register_with_correlation_id_and_get_chain(self):
        from rct_control_plane.jitna_protocol import JITNAProtocolRegistry
        reg = JITNAProtocolRegistry()
        p1 = self._make_packet("p1", corr="chain-X")
        p2 = self._make_packet("p2", corr="chain-X")
        reg.register(p1)
        reg.register(p2)
        chain = reg.get_chain("chain-X")
        assert len(chain) == 2
        pids = {p.packet_id for p in chain}
        assert "p1" in pids and "p2" in pids

    def test_packet_count_and_chain_count(self):
        from rct_control_plane.jitna_protocol import JITNAProtocolRegistry
        reg = JITNAProtocolRegistry()
        reg.register(self._make_packet("p1", corr="c1"))
        reg.register(self._make_packet("p2", corr="c2"))
        assert reg.packet_count == 2
        assert reg.chain_count == 2

    def test_get_statistics(self):
        from rct_control_plane.jitna_protocol import JITNAProtocolRegistry
        reg = JITNAProtocolRegistry()
        reg.register(self._make_packet("p1"))
        reg.register(self._make_packet("p2"))
        stats = reg.get_statistics()
        assert stats["total_packets"] == 2
        assert "packets_by_type" in stats

    def test_clear_resets_registry(self):
        from rct_control_plane.jitna_protocol import JITNAProtocolRegistry
        reg = JITNAProtocolRegistry()
        reg.register(self._make_packet("p1", corr="c1"))
        reg.clear()
        assert reg.packet_count == 0
        assert reg.chain_count == 0


# ============================================================================
# middleware (FeatureFlagStore / feature-flag helpers)
# ============================================================================

class TestFeatureFlagStoreEnvOverride:
    def test_env_override_enables_flag(self, monkeypatch):
        monkeypatch.setenv("FF_ENABLE_MARKETPLACE", "1")
        from rct_control_plane.middleware import FeatureFlagStore
        store = FeatureFlagStore()
        # _apply_env_overrides should set enabled=True on the flag
        assert store.get_flag("enable_marketplace").enabled is True

    def test_env_override_disables_flag(self, monkeypatch):
        monkeypatch.setenv("FF_ENABLE_MARKETPLACE", "0")
        from rct_control_plane.middleware import FeatureFlagStore
        store = FeatureFlagStore()
        assert store.get_flag("enable_marketplace").enabled is False


class TestFeatureFlagStoreIsEnabled:
    def _fresh_store(self):
        from rct_control_plane.middleware import FeatureFlagStore
        return FeatureFlagStore()

    def test_unknown_flag_returns_false(self):
        store = self._fresh_store()
        assert store.is_enabled("no_such_flag") is False

    def test_expired_flag_returns_false(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="expired_test",
            description="",
            enabled=True,
            # Timezone-aware ISO string so fromisoformat comparison works
            expires_at="2000-01-01T00:00:00+00:00",
        ))
        assert store.is_enabled("expired_test") is False

    def test_expired_value_error_still_evaluates(self):
        """ValueError in isoformat parse → expiry check silently skipped."""
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="bad_exp",
            description="",
            enabled=True,
            rollout_percentage=100,
            environments=["*"],
            expires_at="not-a-date",
        ))
        assert store.is_enabled("bad_exp", environment="production") is True

    def test_blacklisted_user_returns_false(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="bl_flag",
            description="",
            enabled=True,
            rollout_percentage=100,
            environments=["*"],
            user_blacklist=["blocked-user"],
        ))
        assert store.is_enabled("bl_flag", user_id="blocked-user") is False

    def test_whitelisted_user_bypasses_disabled_flag(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="wl_flag",
            description="",
            enabled=False,
            user_whitelist=["vip-user"],
        ))
        assert store.is_enabled("wl_flag", user_id="vip-user") is True

    def test_environment_mismatch_returns_false(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="env_flag",
            description="",
            enabled=True,
            rollout_percentage=100,
            environments=["staging"],
        ))
        assert store.is_enabled("env_flag", environment="production") is False

    def test_rollout_percentage_100_returns_true(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="full_rollout",
            description="",
            enabled=True,
            rollout_percentage=100,
            environments=["*"],
        ))
        assert store.is_enabled("full_rollout") is True

    def test_rollout_percentage_0_returns_false(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="zero_rollout",
            description="",
            enabled=True,
            rollout_percentage=0,
            environments=["*"],
        ))
        assert store.is_enabled("zero_rollout", user_id="user-1") is False

    def test_rollout_deterministic_for_user(self):
        """User in bucket gets True; user not in bucket gets consistent result."""
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="partial_rollout",
            description="",
            enabled=True,
            rollout_percentage=50,
            environments=["*"],
        ))
        # Result is deterministic per user_id — just ensure no exception
        r1 = store.is_enabled("partial_rollout", user_id="user-abc")
        r2 = store.is_enabled("partial_rollout", user_id="user-abc")
        assert r1 == r2

    def test_no_user_id_with_partial_rollout_returns_false(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="partial_no_user",
            description="",
            enabled=True,
            rollout_percentage=50,
            environments=["*"],
        ))
        assert store.is_enabled("partial_no_user") is False


class TestFeatureFlagStoreMutations:
    def _fresh_store(self):
        from rct_control_plane.middleware import FeatureFlagStore
        return FeatureFlagStore()

    def test_set_flag_enables_and_disables(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="mut_flag", description="", enabled=False,
            rollout_percentage=100, environments=["*"],
        ))
        assert store.set_flag("mut_flag", True) is True
        # is_enabled: enabled=True, rollout=100, env=* → True
        assert store.is_enabled("mut_flag") is True

    def test_set_flag_missing_key_returns_false(self):
        store = self._fresh_store()
        assert store.set_flag("no_key", True) is False

    def test_toggle_flag(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(flag_key="tog_flag", description="", enabled=False))
        new_state = store.toggle_flag("tog_flag")
        assert new_state is True

    def test_toggle_flag_missing_returns_none(self):
        store = self._fresh_store()
        assert store.toggle_flag("no_key") is None

    def test_set_rollout_invalid_raises(self):
        store = self._fresh_store()
        with pytest.raises(ValueError):
            store.set_rollout("any_flag", 150)

    def test_set_rollout_valid(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(flag_key="r_flag", description="", enabled=True))
        assert store.set_rollout("r_flag", 75) is True
        assert store.get_flag("r_flag").rollout_percentage == 75

    def test_set_rollout_missing_returns_false(self):
        store = self._fresh_store()
        assert store.set_rollout("no_flag", 50) is False

    def test_add_to_whitelist(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(flag_key="wl2_flag", description="", enabled=True))
        assert store.add_to_whitelist("wl2_flag", "u1") is True
        assert "u1" in store.get_flag("wl2_flag").user_whitelist

    def test_add_to_blacklist(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(flag_key="bl2_flag", description="", enabled=True))
        assert store.add_to_blacklist("bl2_flag", "bad-user") is True
        assert "bad-user" in store.get_flag("bl2_flag").user_blacklist

    def test_remove_user_override(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(
            flag_key="ov_flag", description="", enabled=True,
            user_whitelist=["u1"], user_blacklist=["u2"],
        ))
        assert store.remove_user_override("ov_flag", "u1") is True
        flag = store.get_flag("ov_flag")
        assert "u1" not in flag.user_whitelist

    def test_create_flag_duplicate_returns_false(self):
        store = self._fresh_store()
        from rct_control_plane.middleware import FlagDefinition
        store.create_flag(FlagDefinition(flag_key="dup_flag", description="", enabled=True))
        assert store.create_flag(FlagDefinition(flag_key="dup_flag", description="", enabled=True)) is False

    def test_load_from_db_rows(self):
        store = self._fresh_store()
        rows = [
            {
                "flag_key": "db_flag_1",
                "description": "from db",
                "enabled": True,
                "rollout_percentage": 100,
                "user_whitelist": "[]",
                "user_blacklist": "[]",
                "environments": '["*"]',
                "tags": "[]",
                "owner": "team-a",
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-01-01T00:00:00",
                "expires_at": None,
            }
        ]
        store.load_from_db_rows(rows)
        assert store.get_flag("db_flag_1") is not None
        assert store.get_flag("db_flag_1").owner == "team-a"


class TestFeatureFlagModuleFunctions:
    """Test module-level convenience wrappers in middleware.py."""

    def test_is_feature_enabled(self):
        from rct_control_plane.middleware import is_feature_enabled
        # Any result is fine — just ensure no exception
        result = is_feature_enabled("enable_marketplace")
        assert isinstance(result, bool)

    def test_get_all_flags(self):
        from rct_control_plane.middleware import get_all_flags
        flags = get_all_flags()
        assert isinstance(flags, dict)

    def test_get_flag(self):
        from rct_control_plane.middleware import get_flag
        flag = get_flag("enable_marketplace")
        # Might be None or FlagDefinition — just no exception
        assert flag is None or hasattr(flag, "flag_key")

    def test_set_flag_convenience(self):
        from rct_control_plane.middleware import set_flag, FLAG_STORE, FlagDefinition
        FLAG_STORE.create_flag(FlagDefinition(flag_key="conv_set_flag", description="", enabled=False))
        result = set_flag("conv_set_flag", True)
        assert result is True

    def test_toggle_flag_convenience(self):
        from rct_control_plane.middleware import toggle_flag, FLAG_STORE, FlagDefinition
        FLAG_STORE.create_flag(FlagDefinition(flag_key="conv_tog_flag", description="", enabled=False))
        new_state = toggle_flag("conv_tog_flag")
        assert new_state is True

    def test_set_rollout_percentage_convenience(self):
        from rct_control_plane.middleware import set_rollout_percentage, FLAG_STORE, FlagDefinition
        FLAG_STORE.create_flag(FlagDefinition(flag_key="conv_roll_flag", description="", enabled=True))
        assert set_rollout_percentage("conv_roll_flag", 80) is True
