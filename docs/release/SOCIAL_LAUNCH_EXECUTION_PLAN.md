# RCT Platform — Social Launch Execution Plan

This plan turns the launch analysis into an execution sequence for the public SDK repository.

---

## Phase 0 — Blockers Before Public Push

Goal: eliminate claim drift and broken public promises.

Tasks:

1. Sync `README.md`, `ROADMAP.md`, `CHANGELOG.md`, `codecov.yml`, and `.github/workflows/ci.yml` to the current canonical checkpoint
2. Confirm the authoritative checkpoint in `docs/testing/TESTING_CANONICAL.md`
3. Validate the repo against the release checklist in `docs/release/RELEASE_READINESS_CHECKLIST.md`
4. Enable required GitHub UI surfaces referenced by the docs

Exit criteria:

- all public numbers agree
- coverage threshold and Codecov target agree
- Discussions and milestone references do not point to missing UI surfaces

---

## Phase 1 — First-Impression Hardening

Goal: make the repo understandable within 60 seconds.

Tasks:

1. Keep the README entry path concise and action-oriented
2. Ensure a 5-minute demo path is visible near the top
3. Keep open-source vs enterprise scope explicit
4. Provide a visible claim-verification path

Exit criteria:

- a new visitor can tell what the repo is, what to try, how to verify it, and where to ask questions without scrolling through the whole document

---

## Phase 2 — Community Activation

Goal: convert traffic into structured conversations.

Tasks:

1. Enable GitHub Discussions
2. Create and pin the two starter threads in `docs/community/DISCUSSIONS_STARTER_THREADS.md`
3. Configure About, Topics, Website, and profile pinning using `docs/community/GITHUB_UI_LAUNCH_CHECKLIST.md`
4. Create roadmap milestones in GitHub Issues

Exit criteria:

- users have a clear support and discussion channel
- roadmap links point to real milestones
- social traffic lands on a repo with visible, maintained community surfaces

---

## Phase 3 — Evidence Governance

Goal: keep future launches from drifting.

Tasks:

1. Run `python scripts/check_claim_sync.py` whenever metrics change
2. Update the testing canonical doc before updating README or release copy
3. Require release prep to pass the release readiness checklist
4. Keep provenance notes updated whenever scope language changes

Exit criteria:

- the repo no longer depends on human memory alone to keep public claims consistent

---

## Phase 4 — Post-Launch Reinforcement

Goal: turn the repository from impressive to durable.

Tasks:

1. Publish reproducibility notes for benchmarks and examples
2. Add visuals for architecture, benchmark summaries, and release highlights
3. Expand FAQ and pinned Discussions based on incoming questions
4. Build external validation loops through examples, integrations, and benchmark methodology

Exit criteria:

- the repo has both technical credibility and public trust flywheel behavior