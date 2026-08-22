# Fesium Social Preview Prompt

Use this only as an optional `Nano Banana 2` comparison against the controlled brand poster. The controlled asset is produced by `scripts/build_brand.py` and remains the source of truth unless a generated result is clearly better.

## Target

- Product: `Fesium`
- Brand mark direction: `Element Tile` - a solid accent square with a tilted orbit and its nucleus knocked out of it in the shell's own graphite
- Canvas: `1280x640`
- Mood: calm, precise, technical, made for people who are still learning

## Visual Rules

- Dark graphite background, `#121419`
- Matte teal accent, `#5DA9B3`. Not neon, and no glow around the mark - the accent was deliberately softened, and the mark carries its weight through mass rather than light
- No repeating texture. The previous poster tiled a faceted pattern that resolved into visible horizontal banding at this size
- Square geometry. Every structural corner in the app is a right angle, and the mark follows
- No UI screenshot, no device mockup
- Only the word `Fesium` and the line `Local dev tools for students and developers`
- Wordmark set in the app's own face, `Atkinson Hyperlegible`, never a substitute

## Prompt

Create a GitHub social preview poster for `Fesium`, an offline-first local dev toolbox for students and developers. Use a deep flat graphite background with no repeating pattern and no visible banding. Centre a solid matte teal square with a tilted elliptical orbit and a round nucleus cut cleanly out of it in the background colour. Place the word `Fesium` below the mark in a heavy grotesque, and one quiet line of subtitle below that. Keep the composition minimal, square-cornered, and precise. No glow, no gradient mesh, no facets, no device mockup, no marketing clutter. Output at `1280x640`.

## Rule

The AI-generated output is optional. If it wins, the geometry still has to come back into `scripts/build_brand.py` so the mark, the banner, the preview and the app icons keep sharing one definition.
