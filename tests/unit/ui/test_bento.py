from pathlib import Path

import pytest

from fesium.ui.widgets.bento import BENTO_COLUMNS, BENTO_GUTTER, resolve_tile_padding


def test_first_tile_sits_flush_against_both_edges():
    padding = resolve_tile_padding(row=0, column=0)

    assert padding == {"padx": (0, 0), "pady": (0, 0)}


def test_a_following_tile_carries_the_gutter_before_it():
    assert resolve_tile_padding(row=0, column=3)["padx"] == (BENTO_GUTTER, 0)
    assert resolve_tile_padding(row=2, column=0)["pady"] == (BENTO_GUTTER, 0)


def test_two_adjacent_tiles_are_exactly_one_gutter_apart():
    """Each gutter belongs to one tile only, or the middle gaps come out double."""
    left = resolve_tile_padding(row=0, column=0)
    right = resolve_tile_padding(row=0, column=6)

    assert left["padx"][1] + right["padx"][0] == BENTO_GUTTER


def test_trailing_edges_never_pad():
    """Padding only ever leads, so the grid stays flush with the view margin."""
    for row in range(3):
        for column in range(BENTO_COLUMNS):
            padding = resolve_tile_padding(row=row, column=column)
            assert padding["padx"][1] == 0
            assert padding["pady"][1] == 0


@pytest.mark.parametrize(
    "column, span",
    [(0, 13), (6, 7), (11, 2), (-1, 4), (0, 0)],
    ids=["over-wide", "overflows-right", "one-past-edge", "negative-column", "zero-span"],
)
def test_place_tile_rejects_spans_that_do_not_fit(column, span):
    """Caught at build time rather than as a silently mangled layout."""
    from fesium.ui.widgets.bento import BentoGrid

    grid = BentoGrid.__new__(BentoGrid)
    grid.columns = BENTO_COLUMNS
    grid.gutter = BENTO_GUTTER

    with pytest.raises(ValueError, match="does not fit"):
        BentoGrid.place_tile(grid, object(), row=0, column=column, span=span)


def test_views_do_not_build_raw_buttons():
    """Every button goes through ui/widgets/Button.

    A raw CTkButton misses the disabled styling, which is how the Run SQL
    button kept rendering unreadable grey-on-accent after the rest were fixed.
    """
    offenders = sorted(
        path.name
        for path in [*Path("src/fesium/ui/views").glob("*.py"), Path("src/fesium/ui/shell.py")]
        if "ctk.CTkButton(" in path.read_text(encoding="utf-8")
    )

    assert offenders == []
