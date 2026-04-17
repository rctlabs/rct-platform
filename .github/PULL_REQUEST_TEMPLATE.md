# Pull Request

## Summary

Describe the change in 2-5 sentences, including the user-facing or developer-facing outcome.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Refactor
- [ ] Documentation
- [ ] Test-only change
- [ ] Security or compliance improvement

## Validation

- [ ] `python -m pytest`
- [ ] `python -m mypy core/ signedai/ rct_control_plane/ --ignore-missing-imports --explicit-package-bases`
- [ ] `python -m bandit -r core/ signedai/ rct_control_plane/ microservices/ -lll`

## Checklist

- [ ] Tests added or updated where behavior changed
- [ ] No credentials, secrets, or internal-only URLs introduced
- [ ] Public docs updated if public behavior changed
- [ ] This PR stays within the public SDK scope

## Notes for Reviewers

List any known tradeoffs, migration concerns, or follow-up work.
