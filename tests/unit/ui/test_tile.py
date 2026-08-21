from fesium.ui.widgets.tile import MAX_META_CHARS, truncate_meta


def test_short_meta_is_left_alone():
    assert truncate_meta("4 columns") == "4 columns"
    assert truncate_meta("") == ""


def test_long_meta_is_truncated():
    """A tile header label is single-line, so it demands its full text width.

    A full PHP version string in that slot stretched its tile from 405px to
    561px and squeezed the tile beside it down to 250px.
    """
    long_meta = "PHP 8.5.2 (cli) (built: Jan 13 2026 21:54:57) (ZTS Visual C++ 2022 x64)"

    truncated = truncate_meta(long_meta)

    assert len(truncated) <= MAX_META_CHARS
    assert truncated.endswith("…")
    assert truncated.startswith("PHP 8.5.2")


def test_truncation_boundary_is_inclusive():
    exact = "x" * MAX_META_CHARS

    assert truncate_meta(exact) == exact
    assert len(truncate_meta(exact + "x")) == MAX_META_CHARS
