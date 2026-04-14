"""
rct_control_plane/middleware.py
================================
Feature Flags Middleware — Day Zero Operations

Provides a fast, in-memory feature flag evaluation engine with:
- Named boolean flags mirroring `rct_feature_flags` DB table
- Percentage-based rollout (deterministic per user_id via hash)
- Per-user whitelist / blacklist overrides
- Environment-aware evaluation
- Env-var hot-override (FF_<FLAG_KEY_UPPER>=1/0)
- Thread-safe read/write
- Admin CRUD API (used by FastAPI routes in api.py)
- `get_all_flags()` for health check introspection

Usage:
    from rct_control_plane.middleware import is_feature_enabled, get_all_flags

    if is_feature_enabled("enable_marketplace", user_id="user-42"):
        # show marketplace
"""

from __future__ import annotations

import hashlib
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

__all__ = [
    "FeatureFlagStore",
    "FlagDefinition",
    "is_feature_enabled",
    "get_all_flags",
    "get_flag",
    "set_flag",
    "toggle_flag",
    "set_rollout_percentage",
    "add_user_to_whitelist",
    "add_user_to_blacklist",
    "remove_user_override",
    "FLAG_STORE",
]

# ============================================================================
# DATA MODEL
# ============================================================================

@dataclass
class FlagDefinition:
    """In-memory representation of a single feature flag."""
    flag_key: str
    description: str
    enabled: bool
    rollout_percentage: int = 0          # 0-100
    user_whitelist: List[str] = field(default_factory=list)
    user_blacklist: List[str] = field(default_factory=list)
    environments: List[str] = field(default_factory=lambda: ["*"])
    owner: str = "platform-team"
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    expires_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flag_key": self.flag_key,
            "description": self.description,
            "enabled": self.enabled,
            "rollout_percentage": self.rollout_percentage,
            "user_whitelist": self.user_whitelist,
            "user_blacklist": self.user_blacklist,
            "environments": self.environments,
            "owner": self.owner,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "expires_at": self.expires_at,
        }


# ============================================================================
# FLAG STORE
# ============================================================================

class FeatureFlagStore:
    """
    Thread-safe in-memory feature flag store.

    At startup, flags are seeded from DEFAULT_FLAGS.
    Env-var overrides are applied on top:
        FF_ENABLE_MARKETPLACE=1   → enables the flag
        FF_ENABLE_MARKETPLACE=0   → disables the flag

    The store is authoritative at runtime; a real DB sync layer can be
    added by calling `load_from_db_rows()` with rows from rct_feature_flags.
    """

    def __init__(self) -> None:
        self._flags: Dict[str, FlagDefinition] = {}
        self._lock = threading.RLock()
        self._seed_defaults()
        self._apply_env_overrides()

    # ------------------------------------------------------------------
    # Seed
    # ------------------------------------------------------------------

    def _seed_defaults(self) -> None:
        """Populate from Day Zero launch defaults (mirrors DB seed data)."""
        _now = datetime.now(timezone.utc).isoformat()
        defaults: List[FlagDefinition] = [
            FlagDefinition(
                flag_key="enable_marketplace",
                description="Toggles the RCT Marketplace listing and discovery features.",
                enabled=False, rollout_percentage=0,
                environments=["production", "staging"],
                owner="platform-team", tags=["launch", "phase-1"],
                created_at=_now, updated_at=_now,
            ),
            FlagDefinition(
                flag_key="enable_payouts",
                description="Unlocks creator payout request submission (bi-monthly K-Cash flow).",
                enabled=False, rollout_percentage=0,
                environments=["production", "staging"],
                owner="finance-team", tags=["launch", "finance"],
                created_at=_now, updated_at=_now,
            ),
            FlagDefinition(
                flag_key="enable_jitna_v2",
                description="Activates Jitna Engine v2 (new intent graph renderer).",
                enabled=False, rollout_percentage=10,
                environments=["staging"],
                owner="kernel-team", tags=["experiment", "v2"],
                created_at=_now, updated_at=_now,
            ),
            FlagDefinition(
                flag_key="enable_public_register",
                description="Opens public registration. FALSE during Spartan-100 phase.",
                enabled=False, rollout_percentage=0,
                environments=["production", "staging"],
                owner="platform-team", tags=["launch", "access"],
                created_at=_now, updated_at=_now,
            ),
            FlagDefinition(
                flag_key="enable_status_page",
                description="Shows the public status page link in the navbar.",
                enabled=True, rollout_percentage=100,
                environments=["*"],
                owner="ops-team", tags=["launch", "observability"],
                created_at=_now, updated_at=_now,
            ),
            FlagDefinition(
                flag_key="enable_discord_bot",
                description="Activates the RCT Discord support bot commands.",
                enabled=False, rollout_percentage=0,
                environments=["production"],
                owner="ops-team", tags=["launch", "support"],
                created_at=_now, updated_at=_now,
            ),
            FlagDefinition(
                flag_key="enable_stripe_live",
                description="Switches Stripe client from test mode to live keys.",
                enabled=False, rollout_percentage=0,
                environments=["production"],
                owner="finance-team", tags=["launch", "finance", "critical"],
                created_at=_now, updated_at=_now,
            ),
            FlagDefinition(
                flag_key="enable_rate_limiting",
                description="Activates per-user API rate limiting middleware.",
                enabled=True, rollout_percentage=100,
                environments=["*"],
                owner="platform-team", tags=["security", "launch"],
                created_at=_now, updated_at=_now,
            ),
            FlagDefinition(
                flag_key="enable_advanced_analytics",
                description="Enables creator analytics dashboard (Phase 2 feature).",
                enabled=False, rollout_percentage=0,
                environments=["staging"],
                owner="platform-team", tags=["phase-2"],
                created_at=_now, updated_at=_now,
            ),
            FlagDefinition(
                flag_key="enable_ab_test_checkout",
                description="A/B tests a simplified checkout flow (10% of users).",
                enabled=False, rollout_percentage=10,
                environments=["staging"],
                owner="growth-team", tags=["experiment", "ab-test"],
                created_at=_now, updated_at=_now,
            ),
        ]
        for f in defaults:
            self._flags[f.flag_key] = f

    def _apply_env_overrides(self) -> None:
        """
        Check environment variables of the form FF_<FLAG_KEY_UPPER>=1|0.
        Example: FF_ENABLE_MARKETPLACE=1 enables enable_marketplace.
        """
        for flag_key in list(self._flags.keys()):
            env_key = f"FF_{flag_key.upper()}"
            val = os.environ.get(env_key)
            if val is not None:
                self._flags[flag_key].enabled = val.strip() not in ("0", "false", "no", "off", "")

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def is_enabled(
        self,
        flag_key: str,
        user_id: Optional[str] = None,
        environment: Optional[str] = None,
    ) -> bool:
        """
        Evaluate a feature flag.

        Evaluation order:
          1. Flag must exist — otherwise returns False (fail-closed).
          2. Flag must not be expired.
          3. Environment targeting.
          4. User blacklist → immediate False.
          5. User whitelist → immediate True.
          6. Flag must have enabled=True.
          7. Percentage rollout (deterministic hash of user_id mod 100).
        """
        env = environment or os.getenv("RCT_ENV", "development")

        with self._lock:
            flag = self._flags.get(flag_key)

        if flag is None:
            return False

        # Expiry check — always applies even for whitelisted users
        if flag.expires_at:
            try:
                if datetime.fromisoformat(flag.expires_at) < datetime.now(timezone.utc):
                    return False
            except ValueError:
                pass

        # Blacklist — always blocks (even whitelist can't override a blacklist)
        if user_id and user_id in flag.user_blacklist:
            return False

        # Whitelist — bypasses environment targeting, enabled state, and rollout %
        # Use case: allowing Spartan-100 users onto a flag before public rollout
        if user_id and user_id in flag.user_whitelist:
            return True

        # Environment check — after whitelist so whitelisted users can cross envs
        if "*" not in flag.environments and env not in flag.environments:
            return False

        # Base enabled (globally off = off for everyone not whitelisted)
        if not flag.enabled:
            return False

        # Percentage rollout
        if flag.rollout_percentage >= 100:
            return True
        if flag.rollout_percentage <= 0:
            return False

        if user_id:
            # Deterministic bucket: SHA-256(flag_key + user_id) mod 100
            digest = hashlib.sha256(f"{flag_key}:{user_id}".encode()).hexdigest()
            bucket = int(digest[:8], 16) % 100
            return bucket < flag.rollout_percentage

        # No user_id → treat as 0% threshold → disabled
        return False

    # ------------------------------------------------------------------
    # Snapshots
    # ------------------------------------------------------------------

    def get_all(self) -> Dict[str, bool]:
        """Return {flag_key: enabled_bool} snapshot (no user context)."""
        with self._lock:
            return {k: v.enabled for k, v in self._flags.items()}

    def get_flag(self, flag_key: str) -> Optional[FlagDefinition]:
        with self._lock:
            return self._flags.get(flag_key)

    def list_flags(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [f.to_dict() for f in self._flags.values()]

    # ------------------------------------------------------------------
    # Mutations (admin operations)
    # ------------------------------------------------------------------

    def set_flag(self, flag_key: str, enabled: bool) -> bool:
        """Enable or disable a flag. Returns True if flag existed."""
        with self._lock:
            if flag_key not in self._flags:
                return False
            self._flags[flag_key].enabled = enabled
            self._flags[flag_key].updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def toggle_flag(self, flag_key: str) -> Optional[bool]:
        """Toggle a flag. Returns new state, or None if not found."""
        with self._lock:
            if flag_key not in self._flags:
                return None
            self._flags[flag_key].enabled = not self._flags[flag_key].enabled
            self._flags[flag_key].updated_at = datetime.now(timezone.utc).isoformat()
            return self._flags[flag_key].enabled

    def set_rollout(self, flag_key: str, percentage: int) -> bool:
        """Set rollout percentage (0-100). Returns True on success."""
        if not (0 <= percentage <= 100):
            raise ValueError(f"percentage must be 0-100, got {percentage}")
        with self._lock:
            if flag_key not in self._flags:
                return False
            self._flags[flag_key].rollout_percentage = percentage
            self._flags[flag_key].updated_at = datetime.now(timezone.utc).isoformat()
        return True

    def add_to_whitelist(self, flag_key: str, user_id: str) -> bool:
        with self._lock:
            if flag_key not in self._flags:
                return False
            wl = self._flags[flag_key].user_whitelist
            if user_id not in wl:
                wl.append(user_id)
            return True

    def add_to_blacklist(self, flag_key: str, user_id: str) -> bool:
        with self._lock:
            if flag_key not in self._flags:
                return False
            bl = self._flags[flag_key].user_blacklist
            if user_id not in bl:
                bl.append(user_id)
            return True

    def remove_user_override(self, flag_key: str, user_id: str) -> bool:
        """Remove user from both whitelist and blacklist."""
        with self._lock:
            if flag_key not in self._flags:
                return False
            f = self._flags[flag_key]
            f.user_whitelist = [u for u in f.user_whitelist if u != user_id]
            f.user_blacklist = [u for u in f.user_blacklist if u != user_id]
        return True

    def create_flag(self, flag: FlagDefinition) -> bool:
        """Register a new flag. Returns False if key already exists."""
        with self._lock:
            if flag.flag_key in self._flags:
                return False
            if not flag.created_at:
                flag.created_at = datetime.now(timezone.utc).isoformat()
            if not flag.updated_at:
                flag.updated_at = flag.created_at
            self._flags[flag.flag_key] = flag
        return True

    def load_from_db_rows(self, rows: List[Dict[str, Any]]) -> None:
        """
        Bulk-load flags from DB rows (e.g., from PostgreSQL query results).
        Each row must have keys matching FlagDefinition fields.
        Existing flags are replaced.
        """
        import json as _json
        with self._lock:
            for row in rows:
                key = row["flag_key"]
                whitelist = row.get("user_whitelist", "[]")
                blacklist = row.get("user_blacklist", "[]")
                envs = row.get("environments", '["*"]')
                tags = row.get("tags", "[]")
                try:
                    whitelist = _json.loads(whitelist) if isinstance(whitelist, str) else whitelist
                    blacklist = _json.loads(blacklist) if isinstance(blacklist, str) else blacklist
                    envs = _json.loads(envs) if isinstance(envs, str) else envs
                    tags = _json.loads(tags) if isinstance(tags, str) else tags
                except Exception:
                    pass
                self._flags[key] = FlagDefinition(
                    flag_key=key,
                    description=row.get("description", ""),
                    enabled=bool(row.get("enabled", False)),
                    rollout_percentage=int(row.get("rollout_percentage", 0)),
                    user_whitelist=whitelist,
                    user_blacklist=blacklist,
                    environments=envs,
                    owner=row.get("owner", ""),
                    tags=tags,
                    created_at=str(row.get("created_at", "")),
                    updated_at=str(row.get("updated_at", "")),
                    expires_at=row.get("expires_at"),
                )


# ============================================================================
# MODULE-LEVEL SINGLETON + CONVENIENCE FUNCTIONS
# ============================================================================

FLAG_STORE: FeatureFlagStore = FeatureFlagStore()


def is_feature_enabled(
    flag_key: str,
    user_id: Optional[str] = None,
    environment: Optional[str] = None,
) -> bool:
    """
    Convenience wrapper around FLAG_STORE.is_enabled().

    Examples:
        is_feature_enabled("enable_marketplace")          # global check
        is_feature_enabled("enable_jitna_v2", "user-42") # per-user check
    """
    return FLAG_STORE.is_enabled(flag_key, user_id=user_id, environment=environment)


def get_all_flags() -> Dict[str, bool]:
    """Return snapshot of all flags as {key: bool}."""
    return FLAG_STORE.get_all()


def get_flag(flag_key: str) -> Optional[FlagDefinition]:
    return FLAG_STORE.get_flag(flag_key)


def set_flag(flag_key: str, enabled: bool) -> bool:
    return FLAG_STORE.set_flag(flag_key, enabled)


def toggle_flag(flag_key: str) -> Optional[bool]:
    return FLAG_STORE.toggle_flag(flag_key)


def set_rollout_percentage(flag_key: str, percentage: int) -> bool:
    return FLAG_STORE.set_rollout(flag_key, percentage)


def add_user_to_whitelist(flag_key: str, user_id: str) -> bool:
    return FLAG_STORE.add_to_whitelist(flag_key, user_id)


def add_user_to_blacklist(flag_key: str, user_id: str) -> bool:
    return FLAG_STORE.add_to_blacklist(flag_key, user_id)


def remove_user_override(flag_key: str, user_id: str) -> bool:
    return FLAG_STORE.remove_user_override(flag_key, user_id)
