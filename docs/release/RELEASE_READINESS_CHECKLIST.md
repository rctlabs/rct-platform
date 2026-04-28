# RCT Platform — Public Release Readiness Checklist

Use this checklist before any public launch, social media campaign, GitHub Release, or PyPI tag.

---

## 1. Single-Truth Metrics

- [ ] `docs/testing/TESTING_CANONICAL.md` reflects the latest verified checkpoint
- [ ] `README.md` matches the canonical test, skip, and coverage numbers exactly
- [ ] `ROADMAP.md` matches the current checkpoint summary exactly
- [ ] `CHANGELOG.md` includes an `[Unreleased]` summary for the current quality or launch work
- [ ] Any draft release notes or social launch copy use the same numbers as the canonical doc

## 2. CI and Security Gates

- [ ] `.github/workflows/ci.yml` is green on the current default branch
- [ ] `.github/workflows/security-scan.yml` is green on the current default branch
- [ ] `codecov.yml` target matches the intended coverage floor
- [ ] No known secret exposure or credential leak is present in the working tree
- [ ] Dependency CVE scan output has been reviewed

## 3. GitHub UI Configuration

- [ ] About description is set
- [ ] Website is set to `https://rctlabs.co`
- [ ] Topics are configured for discovery
- [ ] GitHub Discussions is enabled if the repo links to Discussions anywhere in docs or issue templates
- [ ] GitHub Milestones exist for roadmap items referenced in `ROADMAP.md`
- [ ] The repo is pinned on the maintainer profile if it is the launch focal point

See [`../community/GITHUB_UI_LAUNCH_CHECKLIST.md`](../community/GITHUB_UI_LAUNCH_CHECKLIST.md).

## 4. Community Funnel

- [ ] A new visitor can find a 5-minute demo path in `README.md`
- [ ] A new visitor can tell what is open-source vs enterprise-only in under 60 seconds
- [ ] A new visitor can find where to ask questions
- [ ] A new visitor can find how to verify claims
- [ ] A pinned “Start Here” discussion draft is ready if Discussions is enabled

## 5. Release Narrative

- [ ] GitHub Release notes have been drafted from `CHANGELOG.md`
- [ ] Release notes match the current repo state, not an older checkpoint
- [ ] Public-safe provenance is documented
- [ ] Any benchmark or architecture claims link to a reproducible or documented source

See [`PUBLIC_RELEASE_PROVENANCE.md`](PUBLIC_RELEASE_PROVENANCE.md).

## 6. Final Validation Commands

```bash
python scripts/check_claim_sync.py
python -m pytest -q --no-header
python -m pytest --cov=microservices --cov=core --cov=signedai --cov=rct_control_plane --cov-report=term --cov-config=pyproject.toml -q --no-header
python -m pytest microservices -q --no-header
ruff check core/ signedai/ rct_control_plane/ microservices/
```

If any of these commands fail, the launch is not release-ready.