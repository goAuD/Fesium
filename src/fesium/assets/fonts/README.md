# Fesium Bundled Fonts

These font files are bundled so the app stays offline-first and never depends on a CDN or any runtime network access.

## Bundled Families

- `AtkinsonHyperlegible-Regular.ttf` and `AtkinsonHyperlegible-Bold.ttf`
  - Role: everything the app writes - headings, body, labels, metrics, badges
  - Source: Google Fonts repository
  - Upstream path: `ofl/atkinsonhyperlegible/`

- `JetBrainsMono-Regular.ttf`
  - Role: the server log and the SQL editor
  - Source: JetBrains Mono repository
  - Upstream path: `fonts/ttf/JetBrainsMono-Regular.ttf`

## Why Atkinson Hyperlegible

Fesium is for students, so the face is chosen on whether a beginner can read it without getting it wrong - not on how it feels. Atkinson Hyperlegible was drawn by the Braille Institute specifically so that confusable characters stay apart, and it is the only candidate considered with a dotted zero. Fesium's screens are ports, process ids, row counts and file paths, so the zero is the character that costs the most when it is misread.

Five faces were measured at 16px, the app's body size: each confusable pair rendered, centred on its own ink and compared as a shape, scored as a Jaccard distance where 1.00 means the two share nothing.

| Face | Mean separation | Worst pair | Score |
| --- | --- | --- | --- |
| Sora | 0.41 | `l` / `1` | 0.10 |
| IBM Plex Sans | 0.52 | `I` / `1` | 0.28 |
| Atkinson Hyperlegible | 0.51 | `rn` / `m` | 0.17 |
| Source Sans 3 | 0.62 | `I` / `l` | 0.08 |
| Public Sans | 0.59 | `I` / `l` | 0.25 |

**Read the worst pair, not the mean.** A reader is not tripped by an average, they are tripped by the one pair a face gets wrong - which is why Source Sans 3 took the best mean and was still disqualified. The shape score also undersells Atkinson on purpose: a crossbar or a dot in a zero is exactly the cue a reader uses and barely moves a pixel-overlap number, which is why the specimens were read by eye alongside the table.

Sora was dropped rather than reassigned. Its `l` and `1` measured 0.10 apart, the worst pair of any candidate, and it was setting 12px tile titles - work a display face was never drawn for.

## Why Two Files, Not One Variable Font

The previous bundle shipped `Sora[wght].ttf` and `IBMPlexSans[wdth,wght].ttf`, both variable. Windows exposes a variable font's *named instances* to GDI as separate families (`Sora`, `Sora SemiBold`, `Sora Light`, and so on), so asking Tk for a bold did resolve to a real bold face - but the arrangement only worked because those instances happened to exist. Atkinson ships as static Regular and Bold, which is the plain case: two files, two faces, no instancing involved. Both are listed in `font_manifest.py`, because the loader registers exactly what the manifest points at.

## Local License Texts

Full upstream license texts for the bundled binaries are stored under `licenses/`.
