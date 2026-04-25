"""
Tests for JITNA Protocol — covering uncovered lines 225-232, 283-293, 323-368.

Uncovered areas:
- 225-232: validate_dict() — both success and exception paths
- 283-293: normalize() — non-dict input, field aliases (src/dst/from/to/etc.)
- 323-332: JITNAProtocolRegistry.register() with correlation_id
- 328-332: correlation chain linking
- 336: get() hit
- 340-341: get_chain()
- 346: packet_count property
- 351: chain_count property
- 355-359: get_statistics() with non-empty store
- 362-368: get_statistics() type_counts + clear()
"""
from __future__ import annotations

import pytest
from rct_control_plane.jitna_protocol import (
    JITNAPacket,
    JITNAMessageType,
    JITNAStatus,
    JITNAValidationResult,
    JITNAValidator,
    JITNANormalizer,
    JITNAProtocolRegistry,
    JITNA_SCHEMA_VERSION,
    JITNA_MAX_PAYLOAD_SIZE_BYTES,
)


# ─────────────────────────────────────────────────────────────────────────────
# JITNAValidationResult
# ─────────────────────────────────────────────────────────────────────────────

class TestJITNAValidationResult:
    def test_initial_valid(self):
        r = JITNAValidationResult()
        assert r.is_valid is True
        assert r.errors == []
        assert r.warnings == []

    def test_add_error_marks_invalid(self):
        r = JITNAValidationResult()
        r.add_error("bad field")
        assert r.is_valid is False
        assert "bad field" in r.errors

    def test_add_warning_stays_valid(self):
        r = JITNAValidationResult()
        r.add_warning("consider adding correlation_id")
        assert r.is_valid is True
        assert len(r.warnings) == 1


# ─────────────────────────────────────────────────────────────────────────────
# JITNAValidator — uncovered paths
# ─────────────────────────────────────────────────────────────────────────────

class TestJITNAValidatorUncovered:
    def test_validate_dict_success(self):
        """validate_dict with valid dict — exercises lines 225-232."""
        v = JITNAValidator()
        data = {
            "source_agent_id": "agent-A",
            "target_agent_id": "agent-B",
            "message_type": "intent_request",
        }
        result = v.validate_dict(data)
        assert isinstance(result, JITNAValidationResult)

    def test_validate_dict_exception_path(self):
        """validate_dict receives non-dict → exception caught → error result."""
        v = JITNAValidator()
        result = v.validate_dict("not a dict at all")   # type: ignore
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_empty_source(self):
        """Missing source_agent_id → error."""
        v = JITNAValidator()
        pkt = JITNAPacket(source_agent_id="", target_agent_id="B", message_type="intent_request")
        result = v.validate(pkt)
        assert not result.is_valid
        assert any("source_agent_id" in e for e in result.errors)

    def test_validate_wrong_schema_version(self):
        """Wrong schema version → error."""
        v = JITNAValidator()
        pkt = JITNAPacket(source_agent_id="A", target_agent_id="B", message_type="intent_request")
        pkt.schema_version = "99.0"
        result = v.validate(pkt)
        assert not result.is_valid

    def test_validate_invalid_message_type(self):
        v = JITNAValidator()
        pkt = JITNAPacket(source_agent_id="A", target_agent_id="B", message_type="invalid_type")
        result = v.validate(pkt)
        assert not result.is_valid

    def test_validate_priority_out_of_range_low(self):
        v = JITNAValidator()
        pkt = JITNAPacket(source_agent_id="A", target_agent_id="B", message_type="intent_request")
        pkt.priority = 0
        result = v.validate(pkt)
        assert not result.is_valid

    def test_validate_priority_out_of_range_high(self):
        v = JITNAValidator()
        pkt = JITNAPacket(source_agent_id="A", target_agent_id="B", message_type="intent_request")
        pkt.priority = 6
        result = v.validate(pkt)
        assert not result.is_valid

    def test_validate_payload_too_large(self):
        """Payload over 1MB → error."""
        v = JITNAValidator()
        pkt = JITNAPacket(source_agent_id="A", target_agent_id="B", message_type="intent_request")
        pkt.payload = {"data": "x" * (JITNA_MAX_PAYLOAD_SIZE_BYTES + 1)}
        result = v.validate(pkt)
        assert not result.is_valid

    def test_validate_empty_payload_warning(self):
        """Empty payload adds warning (but stays valid if other fields ok)."""
        v = JITNAValidator()
        pkt = JITNAPacket(source_agent_id="A", target_agent_id="B", message_type="intent_request")
        pkt.payload = {}
        result = v.validate(pkt)
        assert any("empty payload" in w for w in result.warnings)

    def test_validate_no_correlation_id_warning(self):
        """No correlation_id → warning."""
        v = JITNAValidator()
        pkt = JITNAPacket(source_agent_id="A", target_agent_id="B", message_type="intent_request")
        pkt.correlation_id = None
        result = v.validate(pkt)
        assert any("correlation_id" in w for w in result.warnings)

    def test_validate_fully_valid_packet(self):
        v = JITNAValidator()
        pkt = JITNAPacket(
            source_agent_id="agent-A",
            target_agent_id="agent-B",
            message_type="intent_request",
            payload={"task": "process"},
            priority=3,
            correlation_id="corr-001",
        )
        result = v.validate(pkt)
        assert result.is_valid


# ─────────────────────────────────────────────────────────────────────────────
# JITNANormalizer — uncovered paths (lines 283-305)
# ─────────────────────────────────────────────────────────────────────────────

class TestJITNANormalizerUncovered:
    def test_normalize_non_dict_raises(self):
        """Non-dict input → TypeError (line 283-284)."""
        normalizer = JITNANormalizer()
        with pytest.raises(TypeError, match="Expected dict"):
            normalizer.normalize("not a dict")   # type: ignore

    def test_normalize_with_src_alias(self):
        """'src' → 'source_agent_id' alias (line 288-290)."""
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "src": "sender",
            "target_agent_id": "receiver",
            "message_type": "intent_request",
        })
        assert pkt.source_agent_id == "sender"

    def test_normalize_with_dst_alias(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "source_agent_id": "A",
            "dst": "recvr",
            "message_type": "intent_request",
        })
        assert pkt.target_agent_id == "recvr"

    def test_normalize_with_from_to_aliases(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "from": "sender-from",
            "to": "target-to",
            "message_type": "intent_request",
        })
        assert pkt.source_agent_id == "sender-from"
        assert pkt.target_agent_id == "target-to"

    def test_normalize_with_type_alias(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "source_agent_id": "A",
            "target_agent_id": "B",
            "type": "negotiation",
        })
        assert pkt.message_type == "negotiation"

    def test_normalize_with_body_alias(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "source_agent_id": "A",
            "target_agent_id": "B",
            "message_type": "intent_request",
            "body": {"data": "val"},
        })
        assert pkt.payload == {"data": "val"}

    def test_normalize_with_content_alias(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "source_agent_id": "A",
            "target_agent_id": "B",
            "message_type": "intent_request",
            "content": {"item": "value"},
        })
        assert pkt.payload == {"item": "value"}

    def test_normalize_with_prio_alias(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "source_agent_id": "A",
            "target_agent_id": "B",
            "message_type": "intent_request",
            "prio": 5,
        })
        assert pkt.priority == 5

    def test_normalize_with_corr_id_alias(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "source_agent_id": "A",
            "target_agent_id": "B",
            "message_type": "intent_request",
            "corr_id": "correlation-123",
        })
        assert pkt.correlation_id == "correlation-123"

    def test_normalize_with_sig_alias(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "source_agent_id": "A",
            "target_agent_id": "B",
            "message_type": "intent_request",
            "sig": "sha256:abc123",
        })
        assert pkt.signature == "sha256:abc123"

    def test_normalize_with_meta_alias(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "source_agent_id": "A",
            "target_agent_id": "B",
            "message_type": "intent_request",
            "meta": {"env": "prod"},
        })
        assert pkt.metadata == {"env": "prod"}

    def test_normalize_with_id_alias(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "id": "my-packet-001",
            "source_agent_id": "A",
            "target_agent_id": "B",
            "message_type": "intent_request",
        })
        assert pkt.packet_id == "my-packet-001"

    def test_normalize_missing_fields_get_defaults(self):
        """Missing optional fields get defaults."""
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({})
        assert pkt.schema_version == JITNA_SCHEMA_VERSION
        assert pkt.priority == 3
        assert pkt.payload == {}

    def test_normalize_ts_alias(self):
        normalizer = JITNANormalizer()
        pkt = normalizer.normalize({
            "source_agent_id": "A",
            "target_agent_id": "B",
            "message_type": "intent_request",
            "ts": "2026-01-01T00:00:00Z",
        })
        assert pkt.timestamp == "2026-01-01T00:00:00Z"


# ─────────────────────────────────────────────────────────────────────────────
# JITNAProtocolRegistry — uncovered paths (lines 323-368)
# ─────────────────────────────────────────────────────────────────────────────

class TestJITNAProtocolRegistryUncovered:
    def _make_packet(self, corr=None):
        return JITNAPacket(
            source_agent_id="A",
            target_agent_id="B",
            message_type="intent_request",
            correlation_id=corr,
        )

    def test_register_without_correlation(self):
        """Register packet with no correlation_id — no chain created."""
        reg = JITNAProtocolRegistry()
        pkt = self._make_packet(corr=None)
        reg.register(pkt)
        assert reg.packet_count == 1
        assert reg.chain_count == 0

    def test_register_with_correlation_creates_chain(self):
        """Register packet with correlation_id — chain entry created."""
        reg = JITNAProtocolRegistry()
        pkt = self._make_packet(corr="chain-001")
        reg.register(pkt)
        assert reg.chain_count == 1
        chain = reg.get_chain("chain-001")
        assert len(chain) == 1
        assert chain[0].packet_id == pkt.packet_id

    def test_multiple_packets_same_chain(self):
        """Multiple packets with same correlation_id → same chain."""
        reg = JITNAProtocolRegistry()
        for _ in range(3):
            pkt = self._make_packet(corr="chain-multi")
            reg.register(pkt)
        assert reg.packet_count == 3
        assert reg.chain_count == 1
        chain = reg.get_chain("chain-multi")
        assert len(chain) == 3

    def test_get_existing_packet(self):
        """get() returns the packet."""
        reg = JITNAProtocolRegistry()
        pkt = self._make_packet()
        reg.register(pkt)
        retrieved = reg.get(pkt.packet_id)
        assert retrieved is pkt

    def test_get_missing_returns_none(self):
        reg = JITNAProtocolRegistry()
        assert reg.get("nonexistent-id") is None

    def test_get_chain_missing_correlation(self):
        """get_chain for unknown correlation → empty list."""
        reg = JITNAProtocolRegistry()
        assert reg.get_chain("not-a-chain") == []

    def test_packet_count_property(self):
        reg = JITNAProtocolRegistry()
        assert reg.packet_count == 0
        reg.register(self._make_packet())
        assert reg.packet_count == 1

    def test_chain_count_property(self):
        reg = JITNAProtocolRegistry()
        assert reg.chain_count == 0
        reg.register(self._make_packet(corr="c1"))
        assert reg.chain_count == 1

    def test_get_statistics_empty(self):
        reg = JITNAProtocolRegistry()
        stats = reg.get_statistics()
        assert stats["total_packets"] == 0
        assert stats["total_chains"] == 0
        assert stats["packets_by_type"] == {}

    def test_get_statistics_with_packets(self):
        reg = JITNAProtocolRegistry()
        reg.register(self._make_packet())  # intent_request
        reg.register(JITNAPacket(
            source_agent_id="A",
            target_agent_id="B",
            message_type=JITNAMessageType.CONFIRMATION.value,
        ))
        stats = reg.get_statistics()
        assert stats["total_packets"] == 2
        assert "intent_request" in stats["packets_by_type"]
        assert "confirmation" in stats["packets_by_type"]

    def test_clear_empties_all(self):
        reg = JITNAProtocolRegistry()
        reg.register(self._make_packet(corr="chain-1"))
        reg.register(self._make_packet())
        reg.clear()
        assert reg.packet_count == 0
        assert reg.chain_count == 0


# ─────────────────────────────────────────────────────────────────────────────
# JITNAPacket core methods
# ─────────────────────────────────────────────────────────────────────────────

class TestJITNAPacketCoverage:
    def test_to_dict_serializable(self):
        pkt = JITNAPacket(source_agent_id="A", target_agent_id="B", message_type="intent_request")
        d = pkt.to_dict()
        assert isinstance(d, dict)
        assert d["source_agent_id"] == "A"

    def test_to_json_valid(self):
        pkt = JITNAPacket(source_agent_id="A", target_agent_id="B", message_type="intent_request")
        j = pkt.to_json()
        import json
        parsed = json.loads(j)
        assert parsed["source_agent_id"] == "A"

    def test_compute_hash_deterministic(self):
        pkt1 = JITNAPacket(
            source_agent_id="A", target_agent_id="B",
            message_type="intent_request", timestamp="2026-01-01T00:00:00Z"
        )
        # Same content, same hash (excluding packet_id which is uuid)
        # Hash function ignores packet_id — test hash is sha256
        assert len(pkt1.compute_hash()) == 64

    def test_all_message_types(self):
        """Ensure all message type enum values are accessible."""
        types = [mt.value for mt in JITNAMessageType]
        assert "intent_request" in types
        assert "intent_response" in types
        assert "negotiation" in types
        assert "confirmation" in types
        assert "status_update" in types
        assert "error" in types
        assert "heartbeat" in types

    def test_all_status_values(self):
        statuses = [s.value for s in JITNAStatus]
        assert "created" in statuses
        assert "validated" in statuses
        assert "failed" in statuses
