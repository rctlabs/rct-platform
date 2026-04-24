"""
P1-C: Security-focused unit tests.

Validates cryptographic integrity, hash chain tamper detection,
input boundary enforcement, and policy security invariants.
"""

import pytest

from rct_control_plane.jitna_protocol import (
    JITNA_MAX_PAYLOAD_SIZE_BYTES,
    JITNAPacket,
    JITNAValidator,
)
from rct_control_plane.signed_execution import (
    generate_keypair,
    sign_packet,
    verify_packet,
    compute_key_fingerprint,
)
from rct_control_plane.observability import (
    AuditTrail,
    ControlPlaneEvent,
    ControlPlaneEventType,
)
from rct_control_plane.replay_engine import (
    compute_execution_hash,
)
from rct_control_plane.control_plane_state import ControlPlaneState, ControlPlanePhase


class TestCryptographicIntegrity:
    """ED25519 signing edge cases and tampering scenarios."""

    def test_invalid_signature_hex_rejected(self):
        _, pub = generate_keypair()
        pkt = JITNAPacket(source_agent_id="a", target_agent_id="b")
        assert verify_packet(pkt, "not_hex", pub) is False

    def test_truncated_signature_rejected(self):
        priv, pub = generate_keypair()
        pkt = JITNAPacket(source_agent_id="a", target_agent_id="b")
        sig = sign_packet(pkt, priv)
        truncated = sig[:32]
        assert verify_packet(pkt, truncated, pub) is False

    def test_cross_key_rejection(self):
        priv_a, pub_a = generate_keypair()
        _, pub_b = generate_keypair()
        pkt = JITNAPacket(source_agent_id="a", target_agent_id="b", payload={"cmd": "exec"})
        sig = sign_packet(pkt, priv_a)
        assert verify_packet(pkt, sig, pub_a) is True
        assert verify_packet(pkt, sig, pub_b) is False

    def test_fingerprint_differs_for_different_keys(self):
        _, pub_a = generate_keypair()
        _, pub_b = generate_keypair()
        assert compute_key_fingerprint(pub_a) != compute_key_fingerprint(pub_b)


class TestAuditTrailTamperDetection:
    """Verify hash chain detects various tampering scenarios."""

    def test_modified_event_data_detected(self):
        trail = AuditTrail()
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_RECEIVED, intent_id="x"))
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_COMPILED, intent_id="x"))
        # Tamper with the event inside the first entry
        trail.entries[0].event.intent_id = "hijacked"
        assert trail.verify_integrity() is False

    def test_swapped_entries_detected(self):
        trail = AuditTrail()
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_RECEIVED))
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.INTENT_COMPILED))
        trail.append(ControlPlaneEvent(event_type=ControlPlaneEventType.GRAPH_BUILT))
        # Swap entries 1 and 2
        trail.entries[1], trail.entries[2] = trail.entries[2], trail.entries[1]
        assert trail.verify_integrity() is False


class TestJITNAInputBoundaries:
    """Enforce payload size limit and field validation."""

    def test_oversized_payload_rejected(self):
        pkt = JITNAPacket(
            source_agent_id="a",
            target_agent_id="b",
            payload={"data": "x" * (JITNA_MAX_PAYLOAD_SIZE_BYTES + 100)},
        )
        validator = JITNAValidator()
        result = validator.validate(pkt)
        assert result.is_valid is False
        assert any("maximum size" in e.lower() or "exceeds" in e.lower() for e in result.errors)

    def test_priority_boundary_values(self):
        validator = JITNAValidator()
        for p in (1, 2, 3, 4, 5):
            pkt = JITNAPacket(source_agent_id="a", target_agent_id="b", priority=p)
            result = validator.validate(pkt)
            assert all("priority" not in e.lower() for e in result.errors)
        for bad in (0, -1, 6, 100):
            pkt = JITNAPacket(source_agent_id="a", target_agent_id="b", priority=bad)
            result = validator.validate(pkt)
            assert result.is_valid is False


class TestReplayHashSecurity:
    """Ensure replay hashes are tamper-resistant."""

    def test_hash_length_sha256(self):
        state = ControlPlaneState(intent_id="sec-1")
        h = compute_execution_hash(state)
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_different_intents_produce_different_hashes(self):
        s1 = ControlPlaneState(intent_id="a")
        s2 = ControlPlaneState(intent_id="b")
        assert compute_execution_hash(s1) != compute_execution_hash(s2)

    def test_transition_changes_hash(self):
        state = ControlPlaneState(intent_id="sec-2")
        h1 = compute_execution_hash(state)
        state.transition_to(ControlPlanePhase.INTENT_COMPILED)
        h2 = compute_execution_hash(state)
        assert h1 != h2
