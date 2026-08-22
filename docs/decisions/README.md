# Architecture Decision Records

Short, dated records of architectural decisions that outlive a single feature.

## Index

| ID | Status | Title |
| --- | --- | --- |
| [0001](0001-preserve-nanoserver-compat.md) | Accepted | Preserve NanoServer Compatibility During Fesium Migration |
| [0002](0002-mysql-through-our-own-view.md) | Accepted | Reach MySQL Through Fesium's Own Database View, Not a Bundled Admin Panel |

## Adding a New ADR

- Name the file `NNNN-short-title.md` where `NNNN` is the next free number.
- Use the existing ADR as a template: Status / Date / Superseded by, then Context, Decision, Consequences, and (optionally) a removal checklist.
- Keep ADRs short. If a topic needs more than two pages, it probably belongs in [../specs/](../specs/).
