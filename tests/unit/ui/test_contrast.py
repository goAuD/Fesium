"""Contrast floor for every colour pairing the UI actually renders.

The disabled button state shipped at roughly 1.05:1 - text.secondary grey on a
full-strength accent fill - because CustomTkinter only swaps the text colour on
a disabled button and leaves the surface alone. Nothing caught it, because a
palette looks fine right up until two tokens land on top of each other.
"""

import pytest

from fesium.ui.theme.styles import get_button_style
from fesium.ui.theme.tokens import COLOR_TOKENS

# WCAG 2.1 AA for normal-size text.
MIN_CONTRAST = 4.5

BUTTON_VARIANTS = ("primary", "secondary", "danger", "danger_secondary", "nav")
SURFACES = ("bg.app", "bg.panel", "bg.panel_alt", "bg.sidebar")
FOREGROUNDS = ("text.primary", "text.secondary", "accent.primary")


def _relative_luminance(hex_color: str) -> float:
    channels = [int(hex_color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    red, green, blue = linear
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    darker, lighter = sorted((_relative_luminance(foreground), _relative_luminance(background)))
    return (lighter + 0.05) / (darker + 0.05)


def test_contrast_ratio_matches_known_values():
    """Guard the helper itself, so a broken formula cannot pass the suite."""
    assert contrast_ratio("#ffffff", "#000000") == pytest.approx(21.0, abs=0.01)
    assert contrast_ratio("#000000", "#000000") == pytest.approx(1.0, abs=0.01)


@pytest.mark.parametrize("variant", BUTTON_VARIANTS)
@pytest.mark.parametrize("enabled", [True, False], ids=["enabled", "disabled"])
def test_button_label_is_readable_on_its_own_surface(variant, enabled):
    style = get_button_style(variant, enabled=enabled)

    ratio = contrast_ratio(style["text_color"], style["fg_color"])

    assert ratio >= MIN_CONTRAST, f"{variant} ({'enabled' if enabled else 'disabled'}) is {ratio:.2f}:1"


@pytest.mark.parametrize("variant", BUTTON_VARIANTS)
def test_disabled_buttons_change_surface_not_just_text(variant):
    """Swapping only the text colour is what produced the unreadable state."""
    enabled = get_button_style(variant, enabled=True)
    disabled = get_button_style(variant, enabled=False)

    assert disabled["fg_color"] != enabled["fg_color"] or variant == "nav"


@pytest.mark.parametrize("surface", SURFACES)
@pytest.mark.parametrize("foreground", FOREGROUNDS)
def test_text_tokens_are_readable_on_every_surface(foreground, surface):
    ratio = contrast_ratio(COLOR_TOKENS[foreground], COLOR_TOKENS[surface])

    assert ratio >= MIN_CONTRAST, f"{foreground} on {surface} is {ratio:.2f}:1"
