# การวิเคราะห์เปรียบเทียบ: rct-platform (Public SDK) vs rct-ecosystem-private (Enterprise)

> วันที่วิเคราะห์: เมษายน 2026  
> สาขาปัจจุบัน: `fixdata-maintenancedata-1504` (commit `3c1e8c5`)

---

## สารบัญ

1. [ภาพรวมตัวเลขสำคัญ](#1-ภาพรวมตัวเลขสำคัญ)
2. [โครงสร้างไฟล์ Python](#2-โครงสร้างไฟล์-python)
3. [การวิเคราะห์ Microservices](#3-การวิเคราะห์-microservices)
4. [การวิเคราะห์ความแตกต่าง 4,849 vs 142 Tests](#4-การวิเคราะห์ความแตกต่าง-4849-vs-142-tests)
5. [โมดูลที่ไม่มี Test Coverage เลยใน Public SDK](#5-โมดูลที่ไม่มี-test-coverage-เลยใน-public-sdk)
6. [ปัญหาที่พบในขณะนี้ (Critical Issues)](#6-ปัญหาที่พบในขณะนี้-critical-issues)
7. [แผนพัฒนา Public SDK — Improvement Roadmap](#7-แผนพัฒนา-public-sdk--improvement-roadmap)
8. [สรุปเชิงกลยุทธ์](#8-สรุปเชิงกลยุทธ์)

---

## 1. ภาพรวมตัวเลขสำคัญ

| ตัวชี้วัด | rct-platform (Public SDK) | rct-ecosystem-private (Enterprise) | อัตราส่วน |
|---|---|---|---|
| Python files | **79** | **1,782** | 4.4% |
| Microservices | **5** | **70** | 7.1% |
| Test files | **7** | **411** | 1.7% |
| Tests (collected) | **142** | **4,849** | 2.9% |
| Test types | unit เท่านั้น | unit + integration + security + performance + chaos + e2e + hypothesis + fuzzing | — |

**ข้อสรุปหลัก:** Public SDK คือ **4.4% ของ codebase ทั้งหมด** — เป็น curated subset ไม่ใช่ repository เต็มรูปแบบ  
แต่สิ่งที่น่ากังวลคือ test coverage ของ SDK นั้น **ต่ำกว่าที่ควรจะเป็น** สำหรับ SDK สาธารณะ

---

## 2. โครงสร้างไฟล์ Python

### Public SDK (79 ไฟล์) — แยกตาม module:

```
core/                    8 files  — delta_engine, fdia, intent_loop, regional_adapter
  └─ ไม่มี tests เลย! (0 test files)

microservices/           54 files — 5 microservices
  └─ analysearch-intent  (10 files, 1 test file)
  └─ crystallizer        (3 files, 1 test file)
  └─ gateway-api         (3 files, 1 test file)
  └─ intent-loop         (3 files, 2 test files)
  └─ vector-search       (11 files, 2 test files)

rct_control_plane/       20 files — DSL, intent compiler, policy, CLI
  └─ ไม่มี tests เลย! (0 test files)

signedai/                4 files  — models, registry, router
  └─ ไม่มี tests เลย! (0 test files)

examples/                3 files  — demo scripts (ไม่จำเป็นต้องมี tests)
scripts/                 1 file   — update_stats_cache.py
```

### Private Enterprise (1,782 ไฟล์) — top-level modules หลัก:

```
rct_platform/microservices/   ~1,000 files — 70 microservices + integration tests
core/                         197 files    — kernel (L2/L3), adapters, billing, protocol, sandbox
tests/                        244 files    — test suite แบบ standalone (26 categories)
tools/                        48 files     — tooling + utilities
specialist-studio/            37 files     — AI specialist backend
scripts/                      35 files     — automation + deployment
integrations/                 29 files     — game mods, external APIs
rct_benchmark/                23 files     — benchmark infrastructure
data/                         20 files     — database layer (RCTDB)
archive/                      20 files     — deprecated code
discord_bot/                  19 files     — Discord integration
rct_control_plane/            19 files     — advanced control plane (superset of public)
```

---

## 3. การวิเคราะห์ Microservices

### Public SDK มี 5 microservices:
| Microservice | ฟังก์ชั่นหลัก | Tests |
|---|---|---|
| analysearch-intent | Semantic search + blueprint generation | 1 test file |
| crystallizer | Data crystallization/normalization | 1 test file |
| gateway-api | API gateway + Genome API | 1 test file |
| intent-loop | Intent execution loop engine | 2 test files |
| vector-search | Vector embedding search (FAISS/Qdrant) | 2 test files |

### Private Enterprise มี 70 microservices (ที่ยังไม่อยู่ใน Public):
**กลุ่ม Algorithm (algo-10 ถึง algo-19) — ไม่มีใน Public เลย:**
- algo-10-sentiment-analysis, algo-11-ner, algo-12-topic-modeling
- algo-13-text-classification, algo-14-question-answering, algo-15-summarization
- algo-16-translation, algo-17-code-generation, algo-18-code-review, algo-19-bug-detection

**กลุ่ม Core Infrastructure:**
- kernel, kernel-api, rctdb, redis-cache, websocket-server, observability
- gateway: jitna-gateway, jitna-generator, slack-gateway

**กลุ่ม AI/ML Advanced:**
- adaptive-prompting, adaptive-timeout, few-shot-learning, fghf-factuality-guard
- graphrag-complete, graph-traversal, mctr-multi-chain-reasoning, meta-algorithm-generator
- reflexion-agent, self-evolving, genesis-engine, rct-diffusion

**กลุ่ม Business Logic:**
- marketplace, admin-console, monitor-console, owner-console, analytics-console
- hrm-controller, cio-optimizer, planning-depth-expander, workflow-orchestrator-v2

**กลุ่ม Other:**
- data-fusion-v2, constraint-satisfaction-solver, itsr-recommender, moip-planner
- halting-detection, abv-confidence-scoring, albas-auto-scaling
- sea-dream, mee-engine, benchmark-suite, hydra-browser, uia-integrations, tvra-video, swcar-web-intelligence

---

## 4. การวิเคราะห์ความแตกต่าง 4,849 vs 142 Tests

### การกระจาย Tests ใน Private (4,849 tests):

**แยกตาม top-level directory:**
```
tests/           : 196 test files (อยู่ใน tests/ directory หลัก ระดับ top)
rct_platform/    : 162 test files (แยกตาม microservice แต่ละตัว)
core/            :  27 test files (kernel layers L2/L3 + runtime)
specialist-studio:   8 test files
tools/           :   7 test files
```

**แยกตาม test type:**
```
Unit tests          : 337 files (82%) — ทดสอบ logic แต่ละ function
Integration tests   :  43 files (10%) — ทดสอบ interaction ระหว่าง components
Performance tests   :  16 files  (4%) — ทดสอบความเร็ว/throughput
Security tests      :  10 files  (2%) — ทดสอบ injection, auth, exploits
Chaos tests         :   5 files  (1%) — ทดสอบ fault tolerance
```

**ใน tests/ directory หลัก แยก sub-category:**
```
tests/unit/                 : 60 files  — core unit tests
tests/kernel/               : 33 files  — kernel layer tests
tests/integration/          : 24 files  — cross-service integration
tests/security/             :  6 files  — security/auth
tests/benchmark_tests/      :  6 files  — benchmarks
tests/hypothesis/           :  5 files  — property-based testing (Hypothesis library)
tests/benchmark/            :  5 files  — additional benchmarks
tests/performance/          :  5 files  — performance measurements
tests/game_ai/              :  4 files  — game AI integration
tests/discord_bot_tests/    :  4 files  — Discord bot
tests/ops_tests/            :  3 files  — operations tests
tests/os_integration/       :  3 files  — OS-level integration
tests/e2e/                  :  1 file   — end-to-end flow
tests/fuzzing/              :  1 file   — fuzz testing
tests/chaos/                :  1 file   — chaos engineering
tests/hypothesis/           :  5 files  — Hypothesis property testing
```

### Public SDK (142 tests) — ทั้งหมดเป็น Unit Tests เท่านั้น:
```
microservices/analysearch-intent/tests/  : unit tests
microservices/crystallizer/tests/        : unit tests
microservices/gateway-api/tests/         : unit tests
microservices/intent-loop/tests/         : unit tests (2 files)
microservices/vector-search/tests/       : unit tests (2 files)
```

### ช่องว่างที่สำคัญที่สุด (Critical Gaps):

| ประเภท Test | Public SDK | Private Enterprise | ช่องว่าง |
|---|---|---|---|
| Unit tests | ✅ 7 files (microservices เท่านั้น) | 337 files | ขาด: core/, rct_control_plane/, signedai/ |
| Integration tests | ❌ 0 | 43 files | ขาดทั้งหมด |
| Security tests | ❌ 0 | 10 files | ขาดทั้งหมด (CRITICAL) |
| Performance tests | ❌ 0 | 16 files | ขาดทั้งหมด |
| Chaos tests | ❌ 0 | 5 files | ขาดทั้งหมด |
| Hypothesis/property | ❌ 0 | 5 files | ขาดทั้งหมด |
| E2E tests | ❌ 0 | 1 file | ขาดทั้งหมด |
| Fuzzing | ❌ 0 | 1 file | ขาดทั้งหมด |

---

## 5. โมดูลที่ไม่มี Test Coverage เลยใน Public SDK

สิ่งนี้คือปัญหาที่ร้ายแรงที่สุดสำหรับ SDK สาธารณะ:

### `rct_control_plane/` — 20 Python files, **0 tests**
ไฟล์ที่ไม่มี test coverage:
- `dsl_parser.py` — DSL parser (6 mypy errors ที่รู้จัก)
- `policy_language.py` — Policy language compiler (7 mypy errors ที่รู้จัก)
- `intent_compiler.py` — Intent compilation engine (3 mypy errors ที่รู้จัก)
- `intent_schema.py` — Intent schema definitions
- `execution_graph_ir.py` — Execution graph IR
- `control_plane_state.py` — State management
- `middleware.py` — Middleware layer
- `observability.py` — Observability hooks
- `replay_engine.py` — Replay/rollback engine
- `jitna_protocol.py` — JITNA protocol
- `cli.py` — CLI interface (2 mypy errors ที่รู้จัก)
- `api.py` — API layer
- `signed_execution.py` — Signed execution
- `intent_templates/` — Template files

### `signedai/` — 4 Python files, **0 tests**
- `core/models.py` — Data models
- `core/registry.py` — AI registry
- `core/router.py` — Router (1 mypy error ที่รู้จัก)

### `core/` — 8 Python files (4 non-init), **0 tests**
- `core/delta_engine/memory_delta.py`
- `core/fdia/fdia.py`
- `core/regional_adapter/regional_adapter.py`
- `core/intent_loop/` (stub only)

**สรุป:** มีเพียง 5 microservices เท่านั้นที่มี tests ใน Public SDK หรือคิดเป็น **54 จาก 79 ไฟล์** (~68%) ที่ไม่มี test coverage เลย

---

## 6. ปัญหาที่พบในขณะนี้ (Critical Issues)

### 🔴 Critical — ต้องแก้ทันที

**Issue 1: Dependabot Vulnerabilities บน default branch**
- 1 HIGH severity vulnerability
- 1 MODERATE severity vulnerability
- ตรวจพบเมื่อ `git push` branch `fixdata-maintenancedata-1504`
- แหล่งที่มา: น่าจะมาจาก `numpy>=1.24.0` หรือ `fastapi>=0.104.0` ใน requirements.txt
- **Action**: ต้อง merge Dependabot PRs หรือ update version constraints

**Issue 2: mypy type errors — 22 errors ใน 7 ไฟล์ (CI: continue-on-error)**
- `rct_control_plane/dsl_parser.py`: 6 errors
- `rct_control_plane/policy_language.py`: 7 errors
- `rct_control_plane/intent_compiler.py`: 3 errors
- `signedai/core/router.py`: 1 error
- `rct_control_plane/cli.py`: 2 errors
- ปัจจุบัน: `continue-on-error: true` ใน CI (workaround)
- **Action**: ต้องแก้ก่อน v1.0.0 stable

**Issue 3: Pydantic v2 Deprecation Warning**
- `microservices/vector-search/app/models/schemas.py:332`
- ใช้ `class Config` แบบเก่า แทนที่จะเป็น `model_config = ConfigDict(...)`
- จะ break ใน Pydantic v3
- **Action**: migrate ไป ConfigDict

### 🟡 High — ควรแก้ก่อน release ถัดไป

**Issue 4: Zero Security Tests**
- SDK ไม่มี security test แม้แต่ไฟล์เดียว
- API endpoints ใน gateway-api/vector-search ไม่ได้ทดสอบ input validation/injection
- **Action**: เพิ่ม security test suite อย่างน้อย 3-5 ไฟล์

**Issue 5: Zero Coverage บน Core Modules**
- `rct_control_plane/` (module ที่ซับซ้อนที่สุดใน SDK) = 0% coverage
- `signedai/` = 0% coverage
- `core/` = 0% coverage
- **Action**: เพิ่ม test suite สำหรับ 3 modules นี้

**Issue 6: pytest-cov ไม่มี minimum threshold**
- CI รัน `--cov=microservices` แต่ไม่มี `--cov-fail-under`
- Coverage อาจตกได้โดยไม่มีใคร notice
- **Action**: เพิ่ม `--cov-fail-under=70`

---

## 7. แผนพัฒนา Public SDK — Improvement Roadmap

### P0 — Critical (ทำทันที, ก่อน merge ไป main)

| # | งาน | ไฟล์ที่เกี่ยวข้อง | ประมาณ |
|---|---|---|---|
| P0-1 | แก้ Dependabot vulnerabilities | requirements.txt | 1-2 ชั่วโมง |
| P0-2 | แก้ Pydantic deprecation | vector-search/app/models/schemas.py | 30 นาที |

### P1 — High (ทำก่อน v1.0.0-alpha stable)

| # | งาน | ไฟล์ที่สร้างใหม่ | ผล |
|---|---|---|---|
| P1-1 | เพิ่ม tests สำหรับ `rct_control_plane/` | `tests/test_control_plane.py` | +20-30 tests |
| P1-2 | เพิ่ม tests สำหรับ `signedai/` | `signedai/tests/test_signedai.py` | +10-15 tests |
| P1-3 | เพิ่ม tests สำหรับ `core/` stdlib | `core/tests/test_core.py` | +10-15 tests |
| P1-4 | แก้ mypy errors ทั้ง 22 | 5 ไฟล์ที่ระบุใน ci.yml | mypy เป็น hard gate |
| P1-5 | เพิ่ม security test suite พื้นฐาน | `tests/security/test_api_security.py` | +5-10 tests |
| P1-6 | เพิ่ม coverage threshold | `.github/workflows/ci.yml` | ป้องกัน regression |

**Effect:** tests จะเพิ่มจาก 142 → ~220-250 tests โดยครอบคลุม 3 modules ที่สำคัญ

### P2 — Medium (ทำใน sprints ถัดไป)

| # | งาน | รายละเอียด |
|---|---|---|
| P2-1 | เพิ่ม integration test suite | ทดสอบ interaction gateway-api → intent-loop → vector-search |
| P2-2 | เพิ่ม performance benchmarks | ใช้รูปแบบจาก private's benchmark-suite |
| P2-3 | เพิ่ม 1-2 microservices ใหม่ | แนะนำ: `algo-15-summarization` หรือ `intent-classification` |
| P2-4 | เพิ่ม Hypothesis property tests | สำหรับ DSL parser + intent compiler |
| P2-5 | ปรับปรุง conftest.py ให้เป็นมาตรฐาน | ปัจจุบันมี 3 รูปแบบต่างกันใน 5 microservices |

### P3 — Low (Backlog)

| # | งาน | รายละเอียด |
|---|---|---|
| P3-1 | เพิ่ม e2e test flow | ทดสอบ complete request cycle ตั้งแต่ gateway ถึง vector store |
| P3-2 | เพิ่ม chaos test examples | Fault injection patterns สำหรับ developers ที่ใช้ SDK |
| P3-3 | Expand `core/` module | เพิ่ม algorithms/, protocol/ stubs ที่มีประโยชน์จาก private |
| P3-4 | เพิ่ม more microservices | adaptive-prompting, few-shot-learning (ถ้าเหมาะสม) |

---

## 8. สรุปเชิงกลยุทธ์

### Public SDK คืออะไรในระบบนิเวศ RCT?

```
rct-ecosystem-private (Enterprise Full Stack)
├── 1,782 Python files
├── 70 microservices  
├── 4,849 tests (unit + integration + security + performance + chaos)
└── ทำงานที่ rctlabs.co (production)

         ↕ curated 4.4%
         
rct-platform (Public SDK)
├── 79 Python files
├── 5 microservices (core building blocks เท่านั้น)  
├── 142 tests (unit only)
└── ใช้โดย developers + researchers ภายนอก (Apache 2.0)
```

### ทำไม Public SDK ถึงมีขนาดเล็กกว่ามาก?

นี่คือ **การออกแบบโดยเจตนา** ไม่ใช่ข้อบกพร่อง:
1. **IP Protection**: algorithms, business logic, และ enterprise integrations อยู่ใน private
2. **Complexity Management**: 70 microservices มี dependencies ซับซ้อนเกินไปสำหรับ external use
3. **Security**: kernel layers L2/L3, billing, และ marketplace ไม่ควรเปิดเผย
4. **SDK Design**: เลือก expose เฉพาะ "building blocks" ที่ useful สำหรับ developers

### จุดแข็งของ Public SDK ปัจจุบัน:
- ✅ โครงสร้าง FastAPI + Pydantic ที่ดี
- ✅ Test infrastructure ที่ใช้งานได้ (pytest-asyncio, pytest-timeout)
- ✅ CI/CD pipeline ที่ครอบคลุม (bandit, mypy, pytest-cov)
- ✅ Documentation ครบ (README, CONTRIBUTING, CHANGELOG, SECURITY)
- ✅ Apache 2.0 license clear + SECURITY.md

### จุดอ่อนที่สำคัญที่สุดที่ต้องแก้:
1. **Zero test coverage บน 3 core modules** (rct_control_plane, signedai, core)
2. **Zero security tests** — ไม่เหมาะสมสำหรับ SDK สาธารณะที่มี API endpoints
3. **22 mypy errors** — บั่นทอน confidence ของ developers ที่จะใช้ SDK
4. **Dependabot vulnerabilities** บน default branch

### เป้าหมายระยะสั้น (ก่อน v1.0.0 stable):
- Tests: 142 → 250+ tests (เพิ่ม core module coverage)
- Coverage: microservices-only → 70%+ overall
- Security: 0 → 5+ security tests  
- Types: 22 errors → 0 errors (remove continue-on-error)
- Dependencies: 0 Dependabot vulnerabilities

---

*รายงานนี้สร้างโดย GitHub Copilot — เมษายน 2026*  
*ข้อมูล: commit `3c1e8c5` บน branch `fixdata-maintenancedata-1504`*
