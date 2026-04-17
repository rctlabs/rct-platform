# Installation

## Requirements

| Requirement | Minimum |
|-------------|---------|
| Python | 3.10+ |
| OS | Linux, macOS, Windows |

---

## From PyPI

```bash
pip install rct-platform
```

Verify the installation:

```bash
python -c "import core; print(core.__version__)"
# → 1.0.1a0

rct --help
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
# → 591 passed, 14 skipped
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
