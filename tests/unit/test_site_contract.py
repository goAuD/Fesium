"""The published site has to stay honest about the app it describes."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_site  # noqa: E402

from fesium._version import __version__  # noqa: E402

SITE = ROOT / "site"
WORKFLOWS = ROOT / ".github" / "workflows"


def test_committed_page_matches_its_generator():
    """The page in ``site/`` is committed, so it can drift from the script.

    Committing it is deliberate: a page that only ever exists inside a CI run
    is one nobody has looked at before it is public. The cost of that choice is
    exactly this failure mode, so it is the one thing worth a test.
    """
    committed = (SITE / "index.html").read_text(encoding="utf-8")

    assert committed == build_site.build(), (
        "site/index.html is out of date - run: python scripts/build_site.py")


def test_stylesheet_has_no_malformed_selector():
    """A browser drops a rule whose selector it cannot parse, in silence.

    This exists because a doubled dot - ``..hero`` - shipped once. The page
    still matched its generator, because the generator had the same typo, so
    the drift test passed while the hero rendered with no padding at all. That
    is the failure mode a generated stylesheet has: whatever is wrong is wrong
    consistently.
    """
    style = re.search(r"<style>(.*?)</style>", (SITE / "index.html").read_text(
        encoding="utf-8"), re.S).group(1)

    malformed = []
    for block in style.split("}"):
        selector = block.split("{")[0]
        # Strip comments and at-rule bodies before looking at the selector.
        selector = re.sub(r"/\*.*?\*/", " ", selector, flags=re.S).strip()
        if not selector or selector.startswith("@"):
            continue
        for one in selector.split(","):
            one = one.strip()
            if not one:
                malformed.append(f"empty selector in {selector!r}")
            elif ".." in one or "##" in one:
                malformed.append(one)
            elif not re.match(r"^[a-zA-Z.#:*\[]", one):
                malformed.append(one)

    assert malformed == [], f"the browser will drop these rules: {malformed}"


def test_screenshots_are_never_narrower_than_the_text_around_them():
    """The figure insets its image; the shots block widens by exactly that.

    `.shot` carries padding and a border, so the picture starts inside the
    column while every paragraph runs its full width. Reported as the
    screenshots looking like the narrow thing on the page, which they were, by
    26px. Two constants that have to agree - the shape of bug this project has
    hit three times now, after a wraplength tied to a typeface and a centring
    offset tied to a font's metrics.

    Nothing here is measured against the viewport. 100vw counts the scrollbar
    and the layout does not, so the first attempt at this was a scrollbar's
    width too wide and pushed the screenshots off the right edge.
    """
    style = re.search(r"<style>(.*?)</style>", (SITE / "index.html").read_text(
        encoding="utf-8"), re.S).group(1)

    # Every .shots rule, not the first one found. The mobile override appears
    # earlier in the stylesheet than the base rule, so matching once checked
    # the wrong one and passed while the base rule was wrong.
    widenings = [int(value) for value in re.findall(
        r"\.shots\{[^}]*?width:calc\(100% \+ (\d+)px\)", style, re.S)]
    assert len(widenings) >= 2, f"expected the base and the overrides, got {widenings}"
    widened = min(widenings)
    # The base rule, not the narrow-screen override that drops the side borders.
    blocks = [block for block in re.findall(r"\.shot\{([^}]*)\}", style)
              if "border:" in block and "padding:" in block]
    assert len(blocks) == 1, f"expected one base .shot rule, found {len(blocks)}"
    inset = (int(re.search(r"padding:(\d+)px", blocks[0]).group(1))
             + int(re.search(r"border:(\d+)px", blocks[0]).group(1)))

    assert widened >= 2 * inset, (
        f"the shots block widens by {widened}px but the figure insets its image "
        f"by {inset}px a side, so the screenshot sits inside the text column")
    # Comments stripped first: the stylesheet explains why 100vw is avoided,
    # and the explanation should not be what trips the check.
    declarations = re.sub(r"/\*.*?\*/", " ", style, flags=re.S)
    assert "100vw" not in declarations, (
        "size the shots against the column, not the viewport")


def test_page_states_the_version_that_is_actually_shipping():
    page = (SITE / "index.html").read_text(encoding="utf-8")

    assert f"Fesium v{__version__}" in page


def test_jekyll_is_disabled():
    """Pages runs Jekyll by default and would try to process the page."""
    assert (SITE / ".nojekyll").exists()


def test_open_graph_image_is_a_real_file():
    """Open Graph needs an absolute URL, so this one asset cannot be inlined."""
    page = (SITE / "index.html").read_text(encoding="utf-8")

    assert 'property="og:image"' in page
    assert (SITE / "social-preview.png").exists()
    assert (SITE / "social-preview.png").read_bytes() == (
        ROOT / "docs" / "assets" / "brand" / "fesium-social-preview.png").read_bytes()


def test_the_page_carries_no_external_asset():
    """Offline-first is the product's posture; the page should not undercut it.

    Google Fonts is the deliberate exception - the app's own faces have to be
    on the page for it to look like the app - so it is named rather than
    allowed by accident.
    """
    page = (SITE / "index.html").read_text(encoding="utf-8")
    hosts = set(re.findall(r'(?:src|href)="https?://([^/"]+)', page))

    assert hosts <= {"fonts.googleapis.com", "fonts.gstatic.com", "github.com",
                     "goaud.github.io"}, f"unexpected external host: {hosts}"


def test_every_workflow_action_is_pinned_to_a_commit():
    """A tag is mutable and its owner can silently repoint it.

    The repo already pins by hand. This is what stops the next workflow from
    quietly not doing so.
    """
    unpinned = []
    for workflow in sorted(WORKFLOWS.glob("*.yml")):
        for number, line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), 1):
            match = re.search(r"uses:\s*(\S+)", line)
            if not match:
                continue
            reference = match.group(1)
            if reference.startswith("./"):
                continue                      # a local composite action
            if not re.fullmatch(r"[^@]+@[0-9a-f]{40}", reference):
                unpinned.append(f"{workflow.name}:{number} {reference}")

    assert unpinned == [], f"pin these to a full commit SHA: {unpinned}"
