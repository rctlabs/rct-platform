# RCT Platform — Public Claim Registry

**Version:** 1.0.2a0  
**Last Updated:** 2026-04-30  
**Authoritative source:** [`docs/testing/TESTING_CANONICAL.md`](../testing/TESTING_CANONICAL.md)

This file is the **single approved wording source** for every public-facing claim about RCT Platform. Before publishing anything on X, HN, Reddit, LinkedIn, or Thai communities, check that all numbers and phrases trace to an entry in this registry.

---

## 1. Approved Technical Claims

### Test Suite
| Claim | Approved Wording | Source |
| --- | --- | --- |
| Total passing tests | **1,193 passed · 0 skipped · 0 failed** | `TESTING_CANONICAL.md §1` |
| Coverage | **94% line coverage** (rounded from 93.69%; exact: 12,180 stmts, 769 missed) | `TESTING_CANONICAL.md §1` |
| Microservice slice | **258 microservice tests passing** | `TESTING_CANONICAL.md §1` |
| Python matrix | **Python 3.10 / 3.11 / 3.12** | `ci.yml` |
| Coverage floor (CI gate) | **90% minimum enforced by CI** | `ci.yml` + `codecov.yml` |

> **Rounding note:** 94% = ceiling of 93.69%. Approved to use "94%" in all public copy. Do NOT claim "95%" or "nearly 95%". If asked for precision, cite "93.7% (rounded to 94% in public copy)".

### Architecture
| Claim | Approved Wording | Source |
| --- | --- | --- |
| Layers | **10-layer architecture** | `README.md`, architecture docs |
| Algorithms | **41-algorithm framework** | `README.md`, `lib/site-config.ts` |
| Genome subsystems | **7 Genome subsystems** | `README.md` |
| SDK license | **Apache 2.0** | `LICENSE`, `pyproject.toml` |
| Status | **public alpha (v1.0.2a0)** | `CHANGELOG.md` |

### Performance (Delta Engine)
| Claim | Approved Wording | Status |
| --- | --- | --- |
| Memory compression | **74% compression ratio** | ⚠️ Internal benchmark only — always add "(internal benchmark, not independently verified)" when citing publicly |
| Hallucination reduction | **measured under FDIA scoring** | ⚠️ Avoid quantitative % claims until third-party validated; use "FDIA score measures grounded confidence" instead |

---

## 2. Approved Status Framing

Use one of these **approved status phrases** in all public communications:

- ✅ `"public alpha — production-hardened architecture, early SDK surface"`
- ✅ `"v1.0.2a0 — open SDK layer of a production system"`
- ✅ `"1,193 tests passing · Apache 2.0 · Python 3.10+"`
- ❌ Do NOT use `"production-ready"` without qualification
- ❌ Do NOT use `"state-of-the-art"` without a benchmark link
- ❌ Do NOT use `"100% hallucination-free"` — not a valid claim
- ❌ Do NOT use `"fastest"` or `"best"` without comparative benchmark

---

## 3. Platform-Specific Approved Copy

### X (Twitter/X)
- Max 280 chars; favor one clear claim + evidence link
- Approved: `"1,193 tests passing · 94% coverage · Apache 2.0 · Python 3.10+ · Public alpha now open: github.com/rctlabs/rct-platform"`
- Avoid: Thread of metrics without a reproducible evidence link

### Hacker News (Ask HN / Show HN)
- Title must be factual; no superlatives
- Approved title: `"Show HN: RCT Platform – Intent-centric AI OS with constitutional architecture (1,193 tests, Apache 2.0)"`
- First comment must include: SSOT test numbers + Colab link + scope boundary table

### Reddit (r/MachineLearning, r/LocalLLaMA, r/Python)
- Lead with the reproducible proof: `python -m pytest -q --no-header`
- Do NOT open with architecture diagrams alone — lead with working code

### LinkedIn
- Professional framing; safe to include 94% coverage + test count
- Include FDIA equation description as "intent confidence scoring"
- Appropriate: include business value + target audience (enterprise AI governance)

### Thai Communities (Pantip, Facebook, LINE Groups)
- Use Thai-language version from `PLATFORM_KITS.md`
- Always include the English GitHub link for international discoverability
- Approved: ภาษาไทย + ตัวเลขยืนยันได้จริง + ลิงก์ Colab demo

---

## 4. What to Do When Asked for a Number Not in This Registry

1. Check `TESTING_CANONICAL.md` for test/coverage updates
2. Check `benchmark/` docs for performance claims
3. If not found → respond with: `"That metric is not in our current public claim set. Here's what we can verify: [cite registered claim]"`
4. Do NOT improvise numbers under pressure in a discussion thread

---

## 5. Drift Audit Schedule

| Check | Frequency | Owner |
| --- | --- | --- |
| Compare README vs TESTING_CANONICAL | Before each launch wave | Maintainer |
| Run `python scripts/check_claim_sync.py` | Before each launch wave | CI / Maintainer |
| Re-run full test suite to verify 1,193 count | Monthly or after any merge to main | CI |
| Update `SITE_LAST_DEPLOY` in `rctlabs-website/app/sitemap.ts` | Every production deploy | Deployer |

---

## 6. Approved Evidence Links

| Purpose | Link |
| --- | --- |
| Repository | `https://github.com/rctlabs/rct-platform` |
| Website | `https://rctlabs.co` |
| Colab playground (no login needed) | `https://colab.research.google.com/github/rctlabs/rct-platform/blob/main/notebooks/rct_playground.ipynb` |
| CI badge (live status) | `https://github.com/rctlabs/rct-platform/actions/workflows/ci.yml` |
| Codecov (live coverage) | `https://app.codecov.io/gh/rctlabs/rct-platform` |
| Testing SSOT | `https://github.com/rctlabs/rct-platform/blob/main/docs/testing/TESTING_CANONICAL.md` |

---

*Changes to this file must be reviewed before the next distribution wave. Any drift from TESTING_CANONICAL.md in §1 must be corrected immediately.*
