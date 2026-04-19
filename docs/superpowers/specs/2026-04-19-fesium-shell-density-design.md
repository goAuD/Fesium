# Fesium Shell Density Design

Date: 2026-04-19
Status: Draft for review
Scope: Small UX-polish milestone after the restored server workflow

## Summary

This milestone improves the baseline desktop usability of the current `Fesium` shell without reopening the architecture. The immediate goal is to make the default window size feel comfortably usable on desktop, especially in the `Server` view, where the control row and log panel should fit without forcing manual window resizing.

The milestone covers:

- a moderate default shell size increase
- a matching typography bump for panel readability
- scrollable content bodies for views that can grow vertically
- a responsive control layout for the `Server` view
- a reusable inset-style panel treatment for Graphite Grid surfaces

The milestone does not change the restored server flow itself. It only improves how that flow is presented and handled in the desktop shell.

## Goals

- Make the default desktop window usable without immediate manual resizing
- Increase panel readability through a modest font-size bump
- Ensure the `Server` view remains usable even when the window becomes smaller
- Preserve `Overview` as a fast, status-first landing screen
- Add more visual depth to panels while staying within the existing Graphite Grid direction

## Non-Goals

- Reworking the interaction model of the server flow
- Adding new controls or server behaviors
- Repositioning `Overview` into an operational control screen
- Introducing heavy animation or decorative visual effects
- Building a general-purpose responsive layout system for every future UI need

## User Experience

### Shell Baseline

The desktop shell should open at a slightly larger baseline size than it does today.

Recommended values:

- default geometry: `1400x960`
- minimum size: `1100x760`

This is intentionally a moderate change. The goal is not to make the app feel oversized, but to reduce the need for immediate manual resizing on normal desktop displays.

### Typography

The existing type ramp is too small for the current panel density. The updated baseline should be:

- `heading`: `24`
- `body`: `14`
- `body_medium`: `14`
- `mono`: `13`

These changes should improve readability without making the shell look inflated or mobile-scaled.

### Overview

`Overview` remains a stable, status-first landing view.

It should continue to emphasize:

- workspace status
- environment health
- quick orientation
- entry points into deeper views

It should not become the first place where scrolling is required under normal desktop use.

### Server

`Server` is the main pressure point for this milestone.

The view must support:

- readable project and runtime details
- a control section that never clips horizontally
- a log panel that remains meaningfully visible in the default desktop size
- vertical scrolling when the available height becomes constrained

The `Logs` panel is a primary operational element and should not be the first element sacrificed when space tightens.

## Layout Strategy

### Scroll Contract

Scrolling should happen inside the content area, not by relying on the user to resize the whole window.

Recommended behavior:

- keep the sidebar fixed
- keep the shell itself static
- allow the main content body to scroll when needed

Views that should adopt the scrollable-body pattern in this milestone:

- `Server`
- `Database`
- `Environment`
- `Settings`

`Overview` should stay comparatively stable and should only scroll if future content genuinely requires it.

### Server Controls

The current single-row five-button layout is too brittle.

Required behavior:

- on comfortable desktop widths, keep the controls in one row
- on narrower widths, reflow them into two rows
- never allow the control row to clip horizontally

This should be handled through explicit layout logic in `ServerView`, not by assuming the shell will always be wide enough.

## Architecture

This is a targeted UI-structure refinement, not a new application layer.

### `src/fesium/ui/shell.py`

Responsibilities in this milestone:

- adopt the new default geometry
- adopt the updated minimum size
- continue acting only as the outer app shell

No new runtime or server logic belongs here.

### `src/fesium/ui/widgets/panel_card.py`

`PanelCard` should become the reusable surface primitive for visual depth.

Recommended support:

- `default`
- `inset`
- `inset_strong`

These are visual surface variants, not behavioral variants.

### New Small Scroll Wrapper

Add one focused reusable widget for scrollable view bodies rather than implementing scroll behavior ad hoc inside every view.

Responsibilities:

- provide a consistent scrollable content container
- preserve the current Graphite Grid background hierarchy
- reduce repeated layout code across `Server`, `Database`, `Environment`, and `Settings`

### `src/fesium/ui/views/server_view.py`

This view should gain:

- the reusable scroll-body container
- responsive control-row layout logic
- the stronger inset treatment for the log panel

It should not gain direct runtime logic.

## Visual Hierarchy

CustomTkinter does not provide real CSS `box-shadow: inset`, so the effect should be simulated through layered surfaces.

Recommended approach:

- keep the current outer card silhouette
- add a darker inner surface treatment for inset variants
- keep borders subtle and consistent with Graphite Grid
- apply the strongest inset treatment to the `Logs` panel
- use a lighter inset treatment for supporting panels where depth helps but should not dominate

The result should feel more refined and tactile, not glossy or ornamental.

## Testing and Verification

This milestone should stay lightweight but explicit.

Expected coverage:

- token tests for the updated type ramp
- widget tests for `PanelCard` surface variants
- `ServerView` tests that cover the responsive control layout helper
- regression coverage that confirms the log panel still renders
- full `pytest` regression
- manual launch check with `python fesium.py`

## Risks and Guardrails

- Do not overcorrect the shell size into an oversized desktop window
- Do not let inset styling flatten the distinction between informational panels and operational panels
- Do not let per-view scroll logic diverge into separate one-off implementations
- Do not solve clipping only by enlarging the window; the layout must still degrade cleanly

## Success Criteria

This milestone is successful when:

- the app opens at a more usable default desktop size
- panel text is noticeably easier to read
- the `Server` view no longer clips its control row
- the log panel remains visible and useful by default
- smaller window sizes degrade through scrolling and button reflow rather than broken layout
- the updated surfaces feel more polished without breaking the established Fesium visual language
