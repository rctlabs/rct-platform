# Contributing to RCT Platform

Thank you for your interest in contributing to the RCT Platform!

## Code of Conduct

By participating in this project, you agree to uphold a respectful and inclusive environment for all contributors.

## How to Contribute

### Reporting Bugs

1. Check [existing issues](https://github.com/rctlabs/rct-platform/issues) first.
2. Open a new issue with a clear title and description.
3. Include steps to reproduce, expected behavior, and actual behavior.
4. Include your Python version and OS.

### Suggesting Features

1. Open an issue with the `[Feature Request]` prefix.
2. Describe the problem you're solving and why it belongs in the core SDK.
3. Include examples of how the feature would be used.

### Submitting Pull Requests

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes.
4. Ensure all tests pass: `python -m pytest`
5. Ensure no new security issues: `bandit -r .`
6. Submit a pull request against `main`.

#### PR Checklist

- [ ] Tests added/updated for new behavior
- [ ] No hardcoded credentials, API keys, or internal server URLs
- [ ] Import paths use the `rct-platform` package structure (not `rct-ecosystem-private`)
- [ ] Code follows existing style (PEP 8, type hints where applicable)
- [ ] Docstrings updated if public API changed

## Development Setup

```bash
# Clone the repository
git clone https://github.com/rctlabs/rct-platform.git
cd rct-platform

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest

# Run security scan
bandit -r core/ signedai/ rct_control_plane/ microservices/
```

## Security

For security vulnerabilities, please see [SECURITY.md](SECURITY.md).
Do **not** open a public issue for security findings.

## License

By contributing, you agree that your contributions will be licensed under the [Apache 2.0 License](LICENSE).

---

## Scope: What Belongs in This SDK vs Enterprise

This repository is the **public SDK layer** of the RCT Ecosystem. Understanding the scope boundary helps you decide where a contribution belongs.

### In scope for this repo (welcome PRs)

- Core algorithm libraries: `core/fdia/`, `core/delta_engine/`, `core/regional_adapter/`
- SignedAI consensus framework: `signedai/core/`
- RCT Control Plane SDK: `rct_control_plane/`
- Reference microservices: `microservices/` (5 services)
- Examples and demos: `examples/`
- Docs and whitepapers: `docs/`
- Test coverage for any of the above
- New regional adapters, new LLM integrations, new SDK utilities

### Not in scope for this repo (enterprise only)

| Feature | Why not here |
|---------|--------------|
| Genome / Creator Profile full API | Proprietary enterprise data model |
| Full 62-microservice stack | Production infrastructure (not open-source) |
| Enterprise dashboard | Proprietary UI |
| Private test suite (4,849 tests) | Covers proprietary modules |
| `rct-ecosystem-private` content | Internal enterprise codebase |

If you're unsure whether your contribution fits the SDK scope, open an issue with the `[Scope Question]` prefix before investing time in a PR.

### Guidance: do not reference private modules

Contributions must not import from `rct-ecosystem-private` or reference internal paths like `artent_engine/`, `farmer/`, `gateway/` (private). Use only what's in this repository.
