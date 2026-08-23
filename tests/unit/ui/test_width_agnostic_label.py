"""The invariant that broke the app twice in three commits.

The pure helpers run everywhere. The widget assertions need a display, so they
skip where there is none - the Ubuntu CI runner has no X server. They carry a
control case: the same scenario with a plain CTkLabel must collapse. If the
control ever stops collapsing, the test is measuring nothing and says so.
"""

import pytest

from fesium.ui.widgets.width_agnostic_label import (
    ELLIPSIS,
    WidthAgnosticLabel,
    elide_to_width,
    with_horizontal_stretch,
)

# --- pure helpers -----------------------------------------------------------


def test_horizontal_stretch_is_added_to_an_empty_sticky():
    assert with_horizontal_stretch("") == "ew"


def test_horizontal_stretch_keeps_the_vertical_component():
    """Replacing the sticky outright would silently re-align the text."""
    assert with_horizontal_stretch("nw") == "enw"
    assert with_horizontal_stretch("s") == "esw"
    assert with_horizontal_stretch("nsew") == "ensw"


def test_horizontal_stretch_is_idempotent():
    once = with_horizontal_stretch("nw")
    assert with_horizontal_stretch(once) == once


def test_elide_leaves_text_that_fits():
    assert elide_to_width("SHORT", 500, len) == "SHORT"


def test_elide_marks_the_cut():
    result = elide_to_width("WORKSPACE READINESS", 10, len)

    assert result.endswith(ELLIPSIS)
    assert len(result) <= 10
    assert result.startswith("WORKSPACE"[: len(result) - 1])


def test_elide_degrades_to_the_ellipsis_alone():
    assert elide_to_width("ANYTHING", 1, len) == ELLIPSIS


def test_elide_handles_empty_text():
    assert elide_to_width("", 10, len) == ""


# --- the widget itself ------------------------------------------------------

CELL_WIDTH = 420
LONG_TEXT = "COLLAPSE ME PLEASE"


@pytest.fixture(scope="session")
def tk_root():
    """One Tk root for the whole session.

    Tk is not reliably re-creatable in a process: destroying a root leaves the
    interpreter in a state where the next CTk() fails with
    'invalid command name tcl_findLibrary', and every test after the first
    would skip for a reason that has nothing to do with the display.
    """
    ctk = pytest.importorskip("customtkinter")
    try:
        root = ctk.CTk()
    except Exception as exc:  # pragma: no cover - depends on the machine
        pytest.skip(f"no display available: {exc}")

    root.geometry(f"{CELL_WIDTH + 80}x260")
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    try:
        yield root
    finally:
        root.destroy()


@pytest.fixture
def holder(tk_root):
    """A fresh container per test, inside the shared root."""
    ctk = pytest.importorskip("customtkinter")
    frame = ctk.CTkFrame(tk_root, fg_color="transparent")
    frame.grid(row=0, column=0, sticky="nsew")
    frame.grid_columnconfigure(0, weight=1, minsize=CELL_WIDTH)
    try:
        yield tk_root, frame
    finally:
        frame.destroy()


def _settle(root):
    # update() would enter the platform event loop, and on the macOS CI runner
    # it sometimes never comes back - four job timeouts were spent inside this
    # call before its traceback said so. update_idletasks() runs the geometry
    # pass these assertions need without ever waiting on the window server.
    for _ in range(6):
        root.update_idletasks()


def test_a_plain_label_with_a_detached_width_collapses(holder):
    """The control. This is the defect, reproduced on purpose.

    If this ever stops collapsing, the test below proves nothing and this one
    fails first to say so.
    """
    ctk = pytest.importorskip("customtkinter")
    root, frame = holder

    control = ctk.CTkLabel(frame, text=LONG_TEXT, anchor="w")
    control._label.configure(width=1)
    control.grid(row=0, column=0, sticky="w")
    _settle(root)

    assert control._label.winfo_width() < 30


def test_width_agnostic_label_fills_its_cell_even_when_gridded_sticky_w(holder):
    """The caller asks for "w"; the widget still has to render at full width."""
    root, frame = holder

    label = WidthAgnosticLabel(frame, text=LONG_TEXT, anchor="w")
    label.grid(row=0, column=0, sticky="w")
    _settle(root)

    assert label._label.winfo_width() > CELL_WIDTH - 40


def test_the_inner_label_asks_for_one_character_and_is_stretched(holder):
    """Both halves of the fix, checked as end state rather than as method calls."""
    root, frame = holder

    label = WidthAgnosticLabel(frame, text=LONG_TEXT, anchor="w")
    label.grid(row=0, column=0)
    _settle(root)

    assert label._label.cget("width") == 1
    sticky = label._label.grid_info()["sticky"]
    assert "e" in sticky and "w" in sticky


def test_a_vertical_anchor_survives_the_stretch(holder):
    """anchor="nw" must stay top-aligned; MetaList relies on it."""
    root, frame = holder

    label = WidthAgnosticLabel(frame, text=LONG_TEXT, anchor="nw")
    label.grid(row=0, column=0)
    _settle(root)

    sticky = label._label.grid_info()["sticky"]
    assert "n" in sticky and "e" in sticky and "w" in sticky


def test_pack_also_stretches(holder):
    ctk = pytest.importorskip("customtkinter")
    root, frame = holder

    strip = ctk.CTkFrame(frame, fg_color="transparent")
    strip.grid(row=1, column=0, sticky="ew")
    label = WidthAgnosticLabel(strip, text=LONG_TEXT, anchor="w")
    label.pack()
    _settle(root)

    assert label.pack_info()["fill"] in ("x", "both")


def test_elide_marks_a_title_that_does_not_fit(holder):
    root, frame = holder

    frame.grid_columnconfigure(0, weight=0, minsize=60)
    label = WidthAgnosticLabel(frame, text="A VERY LONG TILE TITLE INDEED", anchor="w", elide=True)
    label.grid(row=0, column=0)
    _settle(root)

    # Elision listens for <Configure>, which update() would deliver - but
    # update() is the call that hangs on macOS CI. Calling the handler
    # directly exercises the same code path against the real measured width.
    label._apply_elision()

    assert label._label.cget("text").endswith(ELLIPSIS)
