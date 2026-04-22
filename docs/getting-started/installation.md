# Installation

## Requirements

| Requirement | Minimum |
|-------------|---------|
| Python | 3.10+ |
| OS | Linux, macOS, Windows |

---

## From PyPI

!!! warning "Alpha Release — Source Install Required"
    `rct-platform` v1.0.2a0 is in **Public Alpha** and has not yet been published to PyPI.
    Use the **From Source** method below to install.
    PyPI publishing is planned for v1.0.0 stable.

```bash
# Will be available on PyPI at stable release:
pip install rct-platform
```

---

## From Source (Development)

```bash
git clone https://github.com/rctlabs/rct-platform.git
cd rct-platform

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .\.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install the SDK in editable mode
pip install -e .

# Install dev + test dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## Verify with Tests

```bash
pytest --tb=short -q
# → 723 passed in ~3s
```

---

## What Gets Installed

```
rct-platform/
├── core/           ← FDIA engine, Delta engine, Regional adapter
├── signedai/       ← SignedAI consensus, HexaCore registry
├── rct_control_plane/  ← 15-module DSL + intent schema
└── microservices/  ← 5 reference microservices (read-only SDK)
```

The `rct` CLI entry point is registered automatically after installation:

```bash
rct --help
rct compile intent.json
rct graph build --policy default
```

---

## Interactive Playground (No Install)

Run the FDIA + SignedAI demos directly in your browser via Google Colab — no local install required:

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rctlabs/rct-platform/blob/main/notebooks/rct_playground.ipynb)

The notebook walks through:
1. FDIA equation scoring (`F = D^I × A`)
2. SignedAI tier routing
3. Delta Engine compression concept
4. Tier 9 full pipeline

> **Note:** The Colab notebook is included in the `notebooks/` directory of this repository.
