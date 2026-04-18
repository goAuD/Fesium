# Fesium Brand Rollout Design Spec

- Date: 2026-04-18
- Status: Approved for spec review
- Project: GitHub and asset rollout for `Fesium`

## 1. Summary

This spec defines the first public brand rollout for `Fesium` after the phase 1 code migration. The goal is to replace the remaining `NanoServer`-era GitHub branding and visual assets with a coherent `Fesium` identity that matches the approved desktop redesign direction.

The rollout is intentionally brand-first rather than screenshot-first. The source-of-truth asset set is:

- one approved `Pure Orbit` SVG icon
- one brand-only GitHub social preview poster
- one exact GitHub About string and topic set
- one clean repo asset structure that separates runtime assets from repository marketing assets

An updated app screenshot is explicitly a second asset step, not part of the first social preview image.

## 2. Goals

### Brand Goals

- Replace the `NanoServer` GitHub presentation with `Fesium`
- Establish a durable umbrella-brand identity suitable for future toolbox expansion
- Keep the brand visually modern, dark, precise, and restrained
- Avoid generic “dev tool” branding and avoid over-explaining the product in the social preview

### Repo Goals

- Rename the GitHub repository to `Fesium`
- Replace old root image assets with a structured docs asset layout
- Create a clean path for README branding, GitHub social preview, and app icon usage

### Visual Goals

- Use the approved `Pure Orbit` symbol as the core brand mark
- Use a subtle graphite faceted 3D diamond background
- Keep the social preview as a clean brand poster, not a UI collage
- Preserve strong logo breathing room by placing the wordmark below the orbit mark

## 3. Non-Goals

- No website launch in this rollout
- No tagline on the first GitHub social preview image
- No app screenshot embedded into the first social preview poster
- No second competing logo system
- No AI-generated image as the authoritative source asset

## 4. Approved Brand Direction

### Chosen Brand Position

`Fesium` is presented as a future local dev toolbox brand, not as a narrowly described PHP utility.

This means:

- the GitHub brand language should feel expandable
- the icon should feel system-oriented rather than feature-specific
- the repo presentation should not center “alternative to XAMPP” language

### Chosen Symbol Direction

The approved icon family is:

- `Pure Orbit`

This is the cleanest and most future-proof expression of the brand. It is not primarily a monogram and should not rely on a visible `F` shape to be legible.

The icon geometry must communicate:

- a central core
- orbital structure
- system precision
- calm technical confidence

## 5. Visual Language

### Background Direction

The background is not flat tile patterning and not generic grid texture. It must follow the approved reference direction:

- dark graphite
- subtle faceted 3D diamond / pyramid pattern
- low contrast
- elegant light/shadow variation

The background should support the icon and wordmark rather than compete with them.

Approved intensity:

- `Subtle`

The faceted pattern is texture, not hero content.

### Color Direction

The poster should remain aligned with the approved `Graphite Grid` direction:

- deep graphite base
- restrained cyan glow/accent
- soft white text
- no extra color accents beyond the approved palette

## 6. Social Preview Composition

### Chosen Approach

The first GitHub social preview will be:

- `Pure brand poster`

This image contains:

- the `Pure Orbit` brand mark
- the `Fesium` wordmark
- the subtle graphite faceted background

This image does not contain:

- a UI screenshot
- a feature list
- a tagline
- a product card layout

### Final Poster Rules

- The orbit mark is the visual anchor.
- The `Fesium` wordmark sits below the icon, not on top of it.
- The icon and wordmark form a centered vertical composition block.
- The orbit mark is given more visual breathing room than the wordmark.
- The overall composition should match the final approved mockup logic from the visual brainstorming pass.

### Text on the Poster

Approved poster text:

- `Fesium`

No subtitle or tagline should appear in the first social preview poster.

## 7. GitHub Metadata

### Repository Name

Approved repository name:

- `Fesium`

The rename sequence should be:

1. Rename the GitHub repository from `NanoServer` to `Fesium`
2. Update local git remote state if needed
3. Rename the local working folder afterward, not before

### About Text

Approved GitHub About text:

`Offline-first local dev toolbox for students and developers.`

### Homepage

Homepage should remain empty in this rollout unless a real project site or docs site exists.

### Topics

Approved first topic set:

- `offline-first`
- `local-dev`
- `developer-tools`
- `desktop-app`
- `python`
- `customtkinter`
- `php`
- `sqlite`
- `laravel`
- `toolbox`

Topics that should not lead the repo positioning:

- `alternative-to-xampp`
- legacy Nano product-family language
- marketing-heavy or novelty tags

## 8. Asset Structure

### Repository Brand Assets

Repository-level public-facing assets belong under:

```text
docs/assets/brand/
docs/assets/screenshots/
```

Approved brand asset paths:

- `docs/assets/brand/fesium-orbit.svg`
- `docs/assets/brand/fesium-social-preview.png`
- `docs/assets/brand/fesium-social-preview-prompt.md`

Approved screenshot path:

- `docs/assets/screenshots/fesium-overview.png`

### Runtime Assets

Runtime or app-used assets stay under:

```text
src/fesium/assets/
```

If the desktop app needs a derived icon export, it should be placed under a runtime-appropriate location such as:

- `src/fesium/assets/icons/`

The key rule is:

- `docs/assets/` is for repo and publishing assets
- `src/fesium/assets/` is for app runtime assets

## 9. Icon Source of Truth

There should be one master icon source of truth:

- `docs/assets/brand/fesium-orbit.svg`

From that master asset, derived outputs may be created for:

- README usage
- GitHub usage
- app runtime usage
- future app icon export formats

This avoids maintaining multiple slightly different versions of the brand mark.

### Geometry Requirement

The small-size icon export must be corrected so that the central dot is geometrically centered. The approved direction is visually clean, but the small preview exposed an alignment issue that must be fixed before final export.

## 10. Social Preview Production Strategy

### Primary Asset

The primary social preview should be a controlled, manually composed brand asset based on the approved poster direction.

This controlled asset is the source of truth.

### Optional AI Comparison

An optional comparison path is approved:

- create a prompt file for `Nano Banana 2`
- generate one or more alternate social preview candidates
- compare them against the controlled poster

But:

- the AI-generated version is optional
- the AI-generated version does not replace the master branded source asset by default

The prompt file should be stored at:

- `docs/assets/brand/fesium-social-preview-prompt.md`

## 11. README and App Usage

### README

The README should use the new `Fesium` brand assets and stop referencing deleted root images.

The README should prefer:

- SVG logo usage where appropriate
- assets from `docs/assets/brand/`

### App

The desktop app should ultimately use the same `Pure Orbit` icon family, derived from the same master SVG. The app icon export should follow only after the master SVG is finalized.

## 12. Cleanup Rules

Old root brand images should not be restored.

The legacy examples were:

- `nanoserver.png`
- `social_preview.png`

These are replaced by the structured asset layout under `docs/assets/`.

## 13. Implementation Sequence

The approved implementation order is:

1. Create the master `Pure Orbit` SVG
2. Create the final GitHub social preview poster asset
3. Create the optional `Nano Banana 2` prompt file
4. Add the new docs asset folders and files
5. Update README brand asset references
6. Rename the GitHub repository to `Fesium`
7. Update GitHub About and topic metadata
8. Capture and add a new screenshot as a second asset round
9. Derive and wire the runtime/app icon from the master SVG

## 14. Acceptance Criteria

This rollout is complete when:

- the GitHub repository is named `Fesium`
- the About text matches the approved string exactly
- the approved topic set is applied
- the master `Pure Orbit` SVG exists
- the brand social preview PNG exists
- the README references the new brand assets rather than old root images
- the old root images remain removed
- the screenshot asset path is prepared for the next round

