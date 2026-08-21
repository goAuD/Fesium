from pathlib import Path

from fesium.ui.widgets.body_text import MIN_WRAPLENGTH, resolve_wraplength


def test_resolve_wraplength_uses_the_width_it_is_given():
    assert resolve_wraplength(800) == 800


def test_resolve_wraplength_subtracts_inner_padding_on_both_sides():
    assert resolve_wraplength(800, inner_padding=16) == 768


def test_resolve_wraplength_accepts_scaled_float_widths():
    assert resolve_wraplength(758.4) == 758


def test_resolve_wraplength_never_collapses_below_the_floor():
    assert resolve_wraplength(0) == MIN_WRAPLENGTH
    assert resolve_wraplength(-200, inner_padding=16) == MIN_WRAPLENGTH


def test_views_do_not_hardcode_paragraph_wrap_widths():
    """A constant pixel wrap clips text whenever the window is narrower.

    Paragraphs must go through ``BodyText``, which wraps to the width grid
    actually hands the label. The sidebar in ``shell.py`` is the one place a
    constant is correct, because that column has a fixed width.
    """
    offenders = [
        path.name
        for path in sorted(Path("src/fesium/ui/views").glob("*.py"))
        if "wraplength" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []
