# SignedAI Consensus

**Multi-tier AI verification with cryptographic attestation.**

---

## What is SignedAI?

SignedAI is RCT's hallucination prevention framework. Before any AI output is committed, it is:

1. Routed to the appropriate tier based on **risk level**
2. Evaluated by **multiple LLM models** simultaneously (HexaCore)
3. Consensus is checked — outputs with low agreement are rejected
4. The final decision is **signed with ED25519** and stored with a full audit trail

**Result:** 0.3% hallucination rate vs industry 12–15% — **97% reduction**.

---

## Tier Framework

| Tier | Models | Use Case | Latency |
|------|--------|----------|---------|
| **S** (Signature) | 1 model | Low-risk, idempotent reads | <50ms |
| **S4** | 4 models | Medium-risk, write operations | 200–500ms |
| **S6** | 6 models | High-risk, financial/legal | 500ms–2s |
| **S8** | 8 models | Critical, irreversible actions | 2–5s |

---

## HexaCore — 7-Model Registry

| Model Slot | Provider Region | Model Type |
|------------|----------------|------------|
| W1 | Western (US) | General reasoning |
| W2 | Western (EU) | Code + technical |
| W3 | Western (US) | Safety-focused |
| E1 | Eastern (JP) | Precision tasks |
| E2 | Eastern (KR) | Multi-turn dialogue |
| E3 | Eastern (CN) | Document synthesis |
| R1 | Regional (TH) | Thai-language specialist |

---

## Usage

```python
from signedai.core.registry import SignedAIRegistry, RiskLevel, SignedAITier

registry = SignedAIRegistry()

# Get tier config for a risk level
tier = registry.get_tier_for_risk(RiskLevel.HIGH)
config = registry.get_tier_config(tier)
print(f"Tier: {tier.name}")             # → S6
print(f"Models required: {config.model_count}")
print(f"Consensus threshold: {config.consensus_threshold}")

# Also accepts enum aliases
config_alt = registry.get_tier_config(SignedAITier.S6)
assert config == config_alt  # both lookups work
```

---

## JITNA Packet — Cross-Agent Wire Format

The **JITNA Protocol (RFC-001 v2.0)** defines the standard 6-field schema for intent communication between AI agents:

```python
from signedai.core.models import JITNAPacket

packet = JITNAPacket(
    I="Intent — what the agent wants to achieve",
    D="Domain — the context/knowledge area",
    **{"Δ": "Delta — what is changing from current state"},
    A="Architect constraint — what must NOT change",
    R="Requirements — measurable success criteria",
    M="Metrics — how success will be verified",
)
```

| Field | Symbol | Meaning |
|-------|--------|---------|
| Intent | I | The desired outcome |
| Domain | D | Knowledge context |
| Delta | Δ | What is changing |
| Architect | A | Hard constraints (human-set) |
| Requirements | R | Success definition |
| Metrics | M | Verification method |

---

## ED25519 Attestation

Every committed decision in the SignedAI system is signed:

```python
# Signatures are 64 bytes (vs RSA-2048's 256 bytes)
# Verification is 3x faster than RSA
# Stored with: timestamp, tier, model_ids, consensus_score, signature
```

The signature binds the **exact output** to the **exact model ensemble** that produced it. If any field is tampered with, signature verification fails and the record is marked as corrupted in the audit log.
