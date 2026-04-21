# Contributing to Fesium

## Scope

`Fesium` is being rebuilt from the original `NanoServer` codebase into a modular offline-first desktop app. Contributions should preserve that direction: small focused modules, local-first behavior, and security-conscious defaults.

## Getting Started

The contributor docs live under [docs/dev/](docs/dev/):

- [docs/dev/setup.md](docs/dev/setup.md) — install dependencies and run the app
- [docs/dev/testing.md](docs/dev/testing.md) — run the unit suite and CI expectations
- [docs/dev/conventions.md](docs/dev/conventions.md) — code organization, design rules, and security defaults

## Where Things Go

- `src/fesium/core/` for server, database, config, environment, path, detection, and security logic
- `src/fesium/ui/` for navigation, shell, views, widgets, and theme code
- `src/fesium/assets/` for bundled offline assets such as fonts
- `tests/unit/` for unit coverage that mirrors the source layout

Avoid adding new flat root-level runtime modules. The repo is moving toward the `src/` package layout and away from the old monolithic entrypoint pattern.

## Documentation

If your change affects behavior, update the relevant docs:

- [README.md](README.md) for user-facing workflow changes
- [CHANGELOG.md](CHANGELOG.md) for release-facing notes
- [docs/specs/](docs/specs/) and [docs/plans/](docs/plans/) for larger scoped work
- [docs/decisions/](docs/decisions/) when a decision is durable enough to be a rule, not just a plan
