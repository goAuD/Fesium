# Fesium Documentation

This folder is the single entry point for everything that is not source code.

## Layout

```text
docs/
├── assets/        Brand, screenshots, and other binary assets
├── decisions/     Architecture Decision Records (ADRs)
├── dev/           Contributor setup, testing, and conventions
├── plans/         Dated implementation plans (historical + active)
├── release/       Per-version release notes
└── specs/         Dated design specs that back the plans
```

## Start Here

- **New contributor?** Read [dev/setup.md](dev/setup.md) for install and run steps, then [dev/conventions.md](dev/conventions.md) for repo rules.
- **Looking for the roadmap?** See [../ROADMAP.md](../ROADMAP.md).
- **Want a per-release summary?** See [release/](release/).
- **Want architectural context?** Browse [decisions/](decisions/) and, for bigger features, the matching [specs/](specs/) and [plans/](plans/).

## How the Plan/Spec/ADR Split Works

- `specs/` — design intent for a feature before it is built. Dated by the day the design was approved.
- `plans/` — the step-by-step implementation plan derived from a spec. Also dated.
- `decisions/` — short, durable ADRs for architectural choices that outlive a single feature (numbered).
- `release/` — user-facing summary of what shipped in each tagged version.

Plans and specs are **frozen historical records**. If a design changes after it was written, the change is captured in a newer spec or an ADR, not by rewriting the old file.

## Contributor Rules

- Update `README.md` and `CHANGELOG.md` when user-facing behavior changes.
- Add a new entry under `release/` for every tagged version.
- Record durable architectural choices as an ADR under `decisions/`.
- Keep plans and specs under dated filenames (`YYYY-MM-DD-topic-*.md`).
