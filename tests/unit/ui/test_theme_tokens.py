import struct
from pathlib import Path

from fesium.assets.fonts.font_manifest import FONT_FILES
from fesium.ui.theme.styles import resolve_button_style
from fesium.ui.theme.tokens import COLOR_TOKENS, FONT_TOKENS, TEXT_CENTRING_OFFSET

WINDOWS_PLATFORM_ID = 3
FAMILY_NAME_ID = 1


def read_family_name(path: Path) -> str:
    """Read nameID 1 out of a TrueType name table.

    Parsed by hand rather than with fontTools so the suite keeps its promise of
    running on the runtime dependencies alone - the same reason
    test_brand_asset_layout.py reads PNG headers with struct.
    """
    data = path.read_bytes()
    table_count = struct.unpack(">H", data[4:6])[0]
    for index in range(table_count):
        entry = 12 + index * 16
        if data[entry:entry + 4] == b"name":
            offset, _ = struct.unpack(">II", data[entry + 8:entry + 16])
            break
    else:  # pragma: no cover - a TTF without a name table is not a font
        raise AssertionError(f"{path.name} has no name table")

    count, string_offset = struct.unpack(">HH", data[offset + 2:offset + 6])
    for record in range(count):
        base = offset + 6 + record * 12
        platform, _, _, name_id, length, value_offset = struct.unpack(
            ">HHHHHH", data[base:base + 12])
        if platform == WINDOWS_PLATFORM_ID and name_id == FAMILY_NAME_ID:
            start = offset + string_offset + value_offset
            return data[start:start + length].decode("utf-16-be")
    raise AssertionError(f"{path.name} declares no Windows family name")


def test_graphite_grid_color_tokens_include_required_keys():
    required = {
        "bg.app",
        "bg.sidebar",
        "bg.panel",
        "text.primary",
        "accent.primary",
        "accent.success",
        "accent.warning",
        "accent.danger",
    }
    assert required.issubset(COLOR_TOKENS.keys())


def test_font_manifest_points_to_local_files():
    assert FONT_FILES["heading"].name == "AtkinsonHyperlegible-Bold.ttf"
    assert FONT_FILES["body"].name == "AtkinsonHyperlegible-Regular.ttf"
    assert FONT_FILES["body_medium"].name == "AtkinsonHyperlegible-Bold.ttf"
    assert FONT_FILES["mono"].name == "JetBrainsMono-Regular.ttf"
    for role in ("heading", "body", "body_medium", "mono"):
        assert FONT_FILES[role].exists()


def test_every_token_family_is_actually_bundled():
    """A token naming a font the bundle does not carry falls back in silence.

    Tk resolves an unknown family to a default rather than failing, so a typo
    in FONT_TOKENS shows up only as the app quietly rendering in something
    else. Comparing the families the tokens ask for against the families the
    bundled files declare is what makes that loud.
    """
    asked = {token[0] for token in FONT_TOKENS.values()}
    bundled = {read_family_name(path) for path in set(FONT_FILES.values())}

    assert asked == bundled, f"tokens ask for {asked - bundled}, bundle has {bundled}"


def read_vertical_metrics(path: Path) -> tuple[int, int, int, int]:
    """units-per-em, hhea ascent, hhea descent and OS/2 cap height."""
    data = path.read_bytes()
    tables = {}
    for index in range(struct.unpack(">H", data[4:6])[0]):
        entry = 12 + index * 16
        tables[data[entry:entry + 4]] = struct.unpack(">II", data[entry + 8:entry + 16])[0]
    upem = struct.unpack(">H", data[tables[b"head"] + 18:tables[b"head"] + 20])[0]
    ascent, descent = struct.unpack(">hh", data[tables[b"hhea"] + 4:tables[b"hhea"] + 8])
    cap = struct.unpack(">h", data[tables[b"OS/2"] + 88:tables[b"OS/2"] + 90])[0]
    return upem, ascent, descent, cap


def ideal_centring_offset(path: Path, size: int) -> int:
    """The bottom padding this face needs at this size to centre its caps.

    Tk centres a label on the font's line box. Inside that box the block a
    reader sees runs from the cap top to the baseline, with ``ascent - cap``
    above it and ``descent`` below. When those differ the text renders off
    centre by half the difference, and ``pady=(0, n)`` moves it up by ``n/2``.
    """
    upem, ascent, descent, cap = read_vertical_metrics(path)
    above = (ascent - cap) * size / upem
    below = -descent * size / upem
    return max(0, round(above - below))


def test_centring_offset_matches_what_the_bundled_face_needs():
    """The offset is a property of the face, so derive it from the face.

    It was hardcoded to 2 in Button and again in StatusBadge, measured against
    IBM Plex Sans, and swapping the body font left both shoving their text
    upwards. Deriving it here means the next swap fails this test instead of
    shipping.
    """
    for role, size in (("body_medium", 16), ("tile_title", 12)):
        face = FONT_FILES["body_medium" if role == "body_medium" else "heading"]
        ideal = ideal_centring_offset(face, size)
        assert TEXT_CENTRING_OFFSET == ideal, (
            f"{FONT_TOKENS[role][0]} at {size}px wants a {ideal}px offset, "
            f"but TEXT_CENTRING_OFFSET is {TEXT_CENTRING_OFFSET}")


def test_font_tokens_include_expected_roles():
    assert set(FONT_TOKENS.keys()) == {
        "heading",
        "section_heading",
        "tile_title",
        "metric",
        "body",
        "body_medium",
        "meta",
        "mono",
    }


def test_bento_type_scale_keeps_tile_titles_quieter_than_page_titles():
    """Size is the hierarchy in a bento layout, so the tile heading steps back."""
    assert FONT_TOKENS["tile_title"][1] < FONT_TOKENS["section_heading"][1]
    assert FONT_TOKENS["meta"][1] < FONT_TOKENS["body"][1]
    assert FONT_TOKENS["metric"][1] < FONT_TOKENS["heading"][1]


def test_font_tokens_match_shell_density_scale():
    assert FONT_TOKENS["heading"] == ("Atkinson Hyperlegible", 28, "bold")
    assert FONT_TOKENS["section_heading"] == ("Atkinson Hyperlegible", 18, "bold")
    assert FONT_TOKENS["body"] == ("Atkinson Hyperlegible", 16)
    assert FONT_TOKENS["body_medium"] == ("Atkinson Hyperlegible", 16, "bold")
    assert FONT_TOKENS["mono"] == ("JetBrains Mono", 14)


def test_one_family_sets_everything_the_app_writes():
    """Size and weight carry the hierarchy, so the shell needs one family.

    Fesium used a display face for headings and a second face for body text.
    Dropping to one is what lets a tile title be quiet at 12px without looking
    like a different product, and it is what the bento layout already assumes.
    """
    written = {name: token for name, token in FONT_TOKENS.items() if name != "mono"}

    assert {token[0] for token in written.values()} == {"Atkinson Hyperlegible"}


def test_font_license_docs_exist():
    assert Path("src/fesium/assets/fonts/LICENSES.md").exists()
    assert Path("src/fesium/assets/fonts/licenses/AtkinsonHyperlegible-OFL.txt").exists()
    assert Path("src/fesium/assets/fonts/licenses/JetBrainsMono-OFL.txt").exists()


def test_resolve_button_style_primary_is_filled_accent():
    primary = resolve_button_style("primary")

    assert primary["fg_color"] == "accent.primary"
    assert primary["text_color"] == "bg.app"
    assert primary["border_color"] == "accent.primary"
    assert primary["border_width"] == 1


def test_resolve_button_style_secondary_is_ghost_with_accent_border():
    secondary = resolve_button_style("secondary")

    assert secondary["fg_color"] == "bg.panel"
    assert secondary["text_color"] == "accent.primary"
    assert secondary["border_color"] == "accent.primary"
    assert secondary["border_width"] == 1


def test_resolve_button_style_secondary_is_visually_distinct_from_primary():
    primary = resolve_button_style("primary")
    secondary = resolve_button_style("secondary")

    assert primary["fg_color"] != secondary["fg_color"]
    assert primary["text_color"] != secondary["text_color"]


def test_resolve_button_style_danger_uses_danger_accent():
    danger = resolve_button_style("danger")
    danger_secondary = resolve_button_style("danger_secondary")

    assert danger["fg_color"] == "accent.danger"
    assert danger["border_color"] == "accent.danger"
    assert danger_secondary["fg_color"] == "bg.panel"
    assert danger_secondary["text_color"] == "accent.danger"
    assert danger_secondary["border_color"] == "accent.danger"


def test_nav_rows_are_borderless_and_marked_by_fill():
    """Six bordered boxes in a column read as six separate things. The sidebar
    is one surface, so the current row is marked by its fill and text weight."""
    nav = resolve_button_style("nav")
    nav_active = resolve_button_style("nav", active=True)

    assert nav["border_width"] == 0
    assert nav_active["border_width"] == 0
    assert nav_active["fg_color"] != nav["fg_color"]
    assert nav_active["text_color"] != nav["text_color"]


def test_no_shape_pairs_a_radius_with_a_border():
    """A rounded corner and a border cannot coexist cleanly in CustomTkinter.

    The corner arc is an anti-aliased circle glyph and the straight edges are
    hard-edged rectangles, drawn as separate canvas items. Where they meet the
    edges do not line up and the corner renders as two arcs. Every role either
    has square corners or no border.
    """
    from fesium.ui.theme.tokens import SHAPE_TOKENS

    for role in ("tile", "button", "input"):
        radius = SHAPE_TOKENS[f"{role}.radius"]
        border = SHAPE_TOKENS[f"{role}.border"]
        assert radius == 0 or border == 0, f"{role} pairs radius {radius} with border {border}"


def test_badge_keeps_its_capsule():
    """A badge is a CTkLabel, which has no border, so the pill always renders clean."""
    from fesium.ui.theme.tokens import SHAPE_TOKENS

    assert SHAPE_TOKENS["badge.radius"] >= 999
    assert "badge.border" not in SHAPE_TOKENS
