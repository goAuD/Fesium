# Fesium Bundled Fonts

These font files are bundled so the app can remain offline-first and avoid CDN or runtime network dependencies.

## Bundled Families

- `Sora[wght].ttf`
  - Role: headings and high-visibility UI labels
  - Source: Google Fonts repository
  - Upstream path: `ofl/sora/Sora[wght].ttf`

- `IBMPlexSans[wdth,wght].ttf`
  - Role: body text and medium-emphasis UI text
  - Source: Google Fonts repository
  - Upstream path: `ofl/ibmplexsans/IBMPlexSans[wdth,wght].ttf`

- `JetBrainsMono-Regular.ttf`
  - Role: logs and technical surfaces
  - Source: JetBrains Mono repository
  - Upstream path: `fonts/ttf/JetBrainsMono-Regular.ttf`

## Why Variable Fonts Here

The official upstream currently distributes `Sora` and `IBM Plex Sans` as variable TTFs in the repositories we vendored from. Fesium keeps the upstream filenames intact so provenance stays obvious and update-safe.

## Local License Texts

The full upstream license texts for the bundled font binaries are stored under `src/fesium/assets/fonts/licenses/`.
