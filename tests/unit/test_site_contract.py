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
