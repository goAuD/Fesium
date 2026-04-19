# Fesium Brand Rollout Implementation Plan

> **For Codex/Claude:** Use `${SUPERPOWERS_SKILLS_ROOT}/skills/collaboration/executing-plans/SKILL.md` to implement this plan task-by-task.

**Goal:** Complete the first public `Fesium` brand rollout: add the approved logo and social preview assets, clean up legacy public docs, wire the runtime app icon, consolidate dependencies around a single full `requirements.txt`, rename the GitHub repository, prepare the new screenshot asset path, and ship the work as `v2.0.0`.

**Architecture:** Treat `docs/assets/brand/` as the source of truth for repository-facing brand assets and `src/fesium/assets/` as the runtime asset location for the desktop app. Keep the rollout brand-first: create the controlled SVG and PNG assets first, update public docs and metadata second, then add the fresh screenshot as a separate follow-up asset. Consolidate dependencies so `requirements.txt` is the complete install surface, with `requirements-dev.txt` reduced to a compatibility shim or removed only after all references are updated. Do not rename the local workspace folder until the very end, after the session is finished, because the current tooling is rooted in `D:\GitHub\NanoServer`.

**Tech Stack:** Python 3.12, `pytest`, `pathlib`, `xml.etree.ElementTree`, `tkinter`, `customtkinter`, ImageMagick 7 (`magick`), GitHub CLI (`gh`)

---

## Current References

Read these before starting implementation:

- `docs/superpowers/specs/2026-04-18-fesium-brand-rollout-design.md`
- `README.md`
- `ROADMAP.md`
- `DESIGN_SYSTEM.md`
- `src/fesium/app.py`
- `src/fesium/ui/shell.py`

## Guardrails

- The `Pure Orbit` SVG in `docs/assets/brand/` is the only icon source of truth.
- The first GitHub social preview must remain a pure brand poster with only `Fesium` on the image.
- Keep the faceted graphite background subtle; do not introduce loud gradients or extra accent colors.
- Do not restore `nanoserver.png` or `social_preview.png`.
- There is no longer a `Nano product family`; remove or rewrite public-facing traces of that concept.
- The release target for this rollout is `v2.0.0`.
- `requirements.txt` must become the full install list; do not leave important dependencies only in `requirements-dev.txt`.
- Do not rename the local `D:\GitHub\NanoServer` folder until the final manual post-session step.

## Task 1: Brand Asset Scaffold and Root Image Cleanup Contract

**Files:**

- Create: `docs/assets/brand/.gitkeep`
- Create: `docs/assets/screenshots/.gitkeep`
- Create: `tests/unit/test_brand_asset_layout.py`
- Delete if present: `nanoserver.png`
- Delete if present: `social_preview.png`

**Step 1: Write the failing layout contract test**

In `tests/unit/test_brand_asset_layout.py`:

```python
from pathlib import Path


def test_brand_asset_directories_exist():
    assert Path("docs/assets/brand").is_dir()
    assert Path("docs/assets/screenshots").is_dir()


def test_legacy_root_images_are_removed():
    assert not Path("nanoserver.png").exists()
    assert not Path("social_preview.png").exists()
```

**Step 2: Run the layout test to verify it fails**

Run: `python -m pytest tests/unit/test_brand_asset_layout.py -v`

Expected output:

```text
FAILED tests/unit/test_brand_asset_layout.py::test_brand_asset_directories_exist
```

The legacy image assertions may already pass if the files are already deleted in the working tree. That is fine.

**Step 3: Implement the brand asset scaffold**

- Create `docs/assets/brand/.gitkeep`
- Create `docs/assets/screenshots/.gitkeep`
- If `nanoserver.png` or `social_preview.png` still exist, delete them now and keep them deleted

**Step 4: Run the layout test again**

Run: `python -m pytest tests/unit/test_brand_asset_layout.py -v`

Expected output:

```text
tests/unit/test_brand_asset_layout.py::test_brand_asset_directories_exist PASSED
tests/unit/test_brand_asset_layout.py::test_legacy_root_images_are_removed PASSED
```

**Step 5: Commit**

```bash
git add docs/assets/brand/.gitkeep docs/assets/screenshots/.gitkeep tests/unit/test_brand_asset_layout.py nanoserver.png social_preview.png
git commit -m "chore: scaffold Fesium brand asset directories"
```

## Task 2: Master `Pure Orbit` SVG and AI Prompt Source

**Files:**

- Create: `docs/assets/brand/fesium-orbit.svg`
- Create: `docs/assets/brand/fesium-social-preview-prompt.md`
- Modify: `tests/unit/test_brand_asset_layout.py`

**Step 1: Extend the failing contract test**

Append these tests to `tests/unit/test_brand_asset_layout.py`:

```python
import xml.etree.ElementTree as ET


def test_master_icon_svg_exists_and_has_expected_viewbox():
    svg_path = Path("docs/assets/brand/fesium-orbit.svg")
    assert svg_path.exists()

    root = ET.fromstring(svg_path.read_text(encoding="utf-8"))
    assert root.tag.endswith("svg")
    assert root.attrib["viewBox"] == "0 0 512 512"


def test_social_preview_prompt_mentions_required_terms():
    prompt = Path("docs/assets/brand/fesium-social-preview-prompt.md").read_text(encoding="utf-8").lower()
    for token in [
        "fesium",
        "pure orbit",
        "1280x640",
        "faceted",
        "graphite",
        "nano banana 2",
    ]:
        assert token in prompt
```

**Step 2: Run the test file to verify it fails**

Run: `python -m pytest tests/unit/test_brand_asset_layout.py -v`

Expected output:

```text
FAILED tests/unit/test_brand_asset_layout.py::test_master_icon_svg_exists_and_has_expected_viewbox
FAILED tests/unit/test_brand_asset_layout.py::test_social_preview_prompt_mentions_required_terms
```

**Step 3: Add the master `Pure Orbit` SVG**

Create `docs/assets/brand/fesium-orbit.svg` with this exact structure:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" fill="none">
  <defs>
    <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#73F0FF" stop-opacity="0.28" />
      <stop offset="100%" stop-color="#73F0FF" stop-opacity="0" />
    </radialGradient>
  </defs>

  <circle cx="256" cy="256" r="164" stroke="#73F0FF" stroke-opacity="0.28" stroke-width="10" />
  <circle cx="256" cy="256" r="104" stroke="#73F0FF" stroke-opacity="0.28" stroke-width="10" transform="rotate(18 256 256)" />
  <ellipse cx="256" cy="256" rx="186" ry="88" stroke="#73F0FF" stroke-opacity="0.28" stroke-width="10" transform="rotate(-24 256 256)" />

  <circle cx="256" cy="256" r="78" fill="url(#coreGlow)" />
  <circle cx="256" cy="256" r="16" fill="#73F0FF" />
  <circle cx="306" cy="177" r="10" fill="#73F0FF" />
  <circle cx="189" cy="338" r="10" fill="#73F0FF" />
</svg>
```

This is the master source. Do not add text to this file.

**Step 4: Add the `Nano Banana 2` comparison prompt**

Create `docs/assets/brand/fesium-social-preview-prompt.md` with this exact content:

```markdown
# Fesium Social Preview Prompt

Use this only as an optional comparison against the controlled brand poster.

## Target

- Product: `Fesium`
- Brand mark direction: `Pure Orbit`
- Canvas: `1280x640`
- Mood: calm, premium, technical, expandable local dev toolbox

## Visual Rules

- Dark graphite background
- Subtle faceted 3D diamond / pyramid texture
- Cyan accent glow only around the orbit mark
- No UI screenshot
- No tagline
- Only the word `Fesium` on the image
- Keep the orbit mark visually dominant and the wordmark below it

## Prompt

Create a GitHub social preview poster for `Fesium`, an offline-first local dev toolbox for students and developers. Use a deep graphite background with a subtle faceted 3D diamond pattern, not a flat grid. Center a clean `Pure Orbit` symbol with a restrained cyan glow, then place the word `Fesium` below it with generous breathing room. Keep the composition minimal, premium, and precise. No app UI, no device mockup, no tagline, no extra icons, no marketing clutter. Output at `1280x640`.

## Rule

The AI-generated output is optional. The controlled local asset remains the source of truth unless the generated result is clearly better.
```

**Step 5: Run the test file again**

Run: `python -m pytest tests/unit/test_brand_asset_layout.py -v`

Expected output:

```text
4 passed
```

**Step 6: Commit**

```bash
git add docs/assets/brand/fesium-orbit.svg docs/assets/brand/fesium-social-preview-prompt.md tests/unit/test_brand_asset_layout.py
git commit -m "feat: add Fesium master brand assets"
```

## Task 3: Controlled Social Preview Source and PNG Export

**Files:**

- Create: `docs/assets/brand/fesium-social-preview.svg`
- Create: `docs/assets/brand/fesium-social-preview.png`
- Modify: `tests/unit/test_brand_asset_layout.py`

**Step 1: Extend the failing asset test with PNG validation**

Append these helpers and tests to `tests/unit/test_brand_asset_layout.py`:

```python
import struct


def read_png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(8)
        assert signature == b"\x89PNG\r\n\x1a\n"
        length = struct.unpack(">I", handle.read(4))[0]
        assert length == 13
        chunk = handle.read(4)
        assert chunk == b"IHDR"
        width = struct.unpack(">I", handle.read(4))[0]
        height = struct.unpack(">I", handle.read(4))[0]
        return width, height


def test_social_preview_png_matches_github_recommendation():
    png_path = Path("docs/assets/brand/fesium-social-preview.png")
    assert png_path.exists()
    assert png_path.stat().st_size < 1_000_000
    assert read_png_dimensions(png_path) == (1280, 640)


def test_social_preview_source_svg_exists():
    assert Path("docs/assets/brand/fesium-social-preview.svg").exists()
```

**Step 2: Run the test file to verify it fails**

Run: `python -m pytest tests/unit/test_brand_asset_layout.py -v`

Expected output:

```text
FAILED tests/unit/test_brand_asset_layout.py::test_social_preview_png_matches_github_recommendation
FAILED tests/unit/test_brand_asset_layout.py::test_social_preview_source_svg_exists
```

**Step 3: Create the editable poster source**

Create `docs/assets/brand/fesium-social-preview.svg` as a 1280x640 poster source. Use this exact structural pattern:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640" fill="none">
  <defs>
    <radialGradient id="bgGlowA" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(190 90) rotate(48) scale(240 240)">
      <stop stop-color="#73F0FF" stop-opacity="0.08" />
      <stop offset="1" stop-color="#73F0FF" stop-opacity="0" />
    </radialGradient>
    <radialGradient id="bgGlowB" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(1030 110) rotate(48) scale(220 220)">
      <stop stop-color="#73F0FF" stop-opacity="0.05" />
      <stop offset="1" stop-color="#73F0FF" stop-opacity="0" />
    </radialGradient>
  </defs>

  <rect width="1280" height="640" fill="#11151B" />
  <rect width="1280" height="640" fill="url(#bgGlowA)" />
  <rect width="1280" height="640" fill="url(#bgGlowB)" />

  <!-- Faceted graphite diamonds -->
  <g opacity="0.38">
    <path d="M0 0H160L80 80L0 0Z" fill="#1C222A" />
    <path d="M160 0H320L240 80L160 0Z" fill="#20262F" />
    <path d="M320 0H480L400 80L320 0Z" fill="#1A2028" />
    <path d="M480 0H640L560 80L480 0Z" fill="#20262F" />
    <path d="M640 0H800L720 80L640 0Z" fill="#1B2129" />
    <path d="M800 0H960L880 80L800 0Z" fill="#20262F" />
    <path d="M960 0H1120L1040 80L960 0Z" fill="#1A2028" />
    <path d="M1120 0H1280L1200 80L1120 0Z" fill="#20262F" />
  </g>

  <!-- Repeat the same faceted logic downward in a restrained grid -->
  <g opacity="0.18">
    <path d="M0 80L80 0L160 80L80 160L0 80Z" fill="#0F141A" />
    <path d="M160 80L240 0L320 80L240 160L160 80Z" fill="#11161D" />
    <path d="M320 80L400 0L480 80L400 160L320 80Z" fill="#0F141A" />
    <path d="M480 80L560 0L640 80L560 160L480 80Z" fill="#11161D" />
    <path d="M640 80L720 0L800 80L720 160L640 80Z" fill="#0F141A" />
    <path d="M800 80L880 0L960 80L880 160L800 80Z" fill="#11161D" />
    <path d="M960 80L1040 0L1120 80L1040 160L960 80Z" fill="#0F141A" />
    <path d="M1120 80L1200 0L1280 80L1200 160L1120 80Z" fill="#11161D" />
  </g>

  <!-- Centered Pure Orbit mark -->
  <g transform="translate(640 300)">
    <circle r="164" stroke="#73F0FF" stroke-opacity="0.28" stroke-width="10" />
    <circle r="104" stroke="#73F0FF" stroke-opacity="0.28" stroke-width="10" transform="rotate(18)" />
    <ellipse rx="186" ry="88" stroke="#73F0FF" stroke-opacity="0.28" stroke-width="10" transform="rotate(-24)" />
    <circle r="78" fill="#73F0FF" fill-opacity="0.08" />
    <circle r="16" fill="#73F0FF" />
    <circle cx="50" cy="-79" r="10" fill="#73F0FF" />
    <circle cx="-67" cy="82" r="10" fill="#73F0FF" />
  </g>

  <text x="640" y="566" text-anchor="middle" fill="#EEF3F7" font-size="82" font-family="IBM Plex Sans, Arial, sans-serif" font-weight="700" letter-spacing="-3.5">Fesium</text>
</svg>
```

The exact facet layout can be extended beyond this starter structure, but the final asset must keep the approved subtle 3D graphite feel.

**Step 4: Export the final PNG with ImageMagick**

Run:

```bash
magick docs/assets/brand/fesium-social-preview.svg docs/assets/brand/fesium-social-preview.png
```

Then verify:

```bash
magick identify docs/assets/brand/fesium-social-preview.png
```

Expected output should include `1280x640`.

**Step 5: Run the test file again**

Run: `python -m pytest tests/unit/test_brand_asset_layout.py -v`

Expected output:

```text
6 passed
```

**Step 6: Commit**

```bash
git add docs/assets/brand/fesium-social-preview.svg docs/assets/brand/fesium-social-preview.png tests/unit/test_brand_asset_layout.py
git commit -m "feat: add controlled Fesium social preview assets"
```

## Task 4: Public Docs Cleanup and README Brand Integration

**Files:**

- Modify: `README.md`
- Modify: `ROADMAP.md`
- Delete: `DESIGN_SYSTEM.md`
- Modify: `tests/unit/test_brand_asset_layout.py`

**Step 1: Extend the failing public-doc contract**

Append these tests to `tests/unit/test_brand_asset_layout.py`:

```python
def test_readme_uses_new_brand_assets_and_repo_slug():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "docs/assets/brand/fesium-orbit.svg" in readme
    assert "https://github.com/goAuD/Fesium.git" in readme
    assert "cd Fesium" in readme
    assert "nanoserver.png" not in readme
    assert "social_preview.png" not in readme
    assert "NanoServer/" not in readme


def test_roadmap_uses_fesium_name():
    roadmap = Path("ROADMAP.md").read_text(encoding="utf-8")
    assert roadmap.startswith("# Fesium Roadmap")
    assert "NanoServer" not in roadmap


def test_legacy_design_system_doc_is_removed():
    assert not Path("DESIGN_SYSTEM.md").exists()
```

**Step 2: Run the test file to verify it fails**

Run: `python -m pytest tests/unit/test_brand_asset_layout.py -v`

Expected output:

```text
FAILED tests/unit/test_brand_asset_layout.py::test_readme_uses_new_brand_assets_and_repo_slug
FAILED tests/unit/test_brand_asset_layout.py::test_roadmap_uses_fesium_name
FAILED tests/unit/test_brand_asset_layout.py::test_legacy_design_system_doc_is_removed
```

**Step 3: Update the README**

Make these exact README changes:

1. Add the logo near the top:

```markdown
<p align="center">
  <img src="docs/assets/brand/fesium-orbit.svg" width="120" alt="Fesium Pure Orbit logo">
</p>
```

Insert it directly below `# Fesium`.

1. Update installation to:

```bash
git clone https://github.com/goAuD/Fesium.git
cd Fesium
python -m pip install -r requirements.txt
```

1. Change the project layout label from `NanoServer/` to `Fesium/`.

2. Do not add the social preview PNG to the README yet. The logo is enough for the README brand surface.

**Step 4: Rewrite the roadmap and remove the family doc**

- Update `ROADMAP.md` so the title is `# Fesium Roadmap`
- Replace `NanoServer` mentions with `Fesium`
- Keep the actual roadmap items if they still make sense
- Delete `DESIGN_SYSTEM.md` because it is obsolete, conflicts with the approved `Graphite Grid` direction, and still contains the invalid `Nano Product Family` framing

**Step 5: Run the test file again**

Run: `python -m pytest tests/unit/test_brand_asset_layout.py -v`

Expected output:

```text
9 passed
```

**Step 6: Commit**

```bash
git add README.md ROADMAP.md DESIGN_SYSTEM.md tests/unit/test_brand_asset_layout.py
git commit -m "docs: align public repo docs with Fesium brand"
```

## Task 5: Dependency Consolidation Around `requirements.txt`

**Files:**

- Modify: `requirements.txt`
- Modify: `requirements-dev.txt`
- Modify: `.github/workflows/python-tests.yml`
- Modify: `CONTRIBUTING.md`
- Modify: `README.md`
- Create: `tests/unit/test_dependency_contract.py`

**Step 1: Write the failing dependency contract**

Create `tests/unit/test_dependency_contract.py`:

```python
from pathlib import Path


def test_requirements_txt_contains_runtime_and_test_dependencies():
    requirements = Path("requirements.txt").read_text(encoding="utf-8")
    assert "customtkinter" in requirements
    assert "pytest" in requirements


def test_requirements_dev_txt_is_only_a_compatibility_shim():
    requirements_dev = Path("requirements-dev.txt").read_text(encoding="utf-8").strip()
    assert requirements_dev == "-r requirements.txt"


def test_repo_docs_install_from_requirements_txt():
    readme = Path("README.md").read_text(encoding="utf-8")
    contributing = Path("CONTRIBUTING.md").read_text(encoding="utf-8")
    workflow = Path(".github/workflows/python-tests.yml").read_text(encoding="utf-8")

    assert "python -m pip install -r requirements.txt" in readme
    assert "python -m pip install -r requirements.txt" in contributing
    assert "python -m pip install -r requirements.txt" in workflow
```

**Step 2: Run the dependency contract to verify it fails**

Run: `python -m pytest tests/unit/test_dependency_contract.py -v`

Expected output:

```text
FAILED tests/unit/test_dependency_contract.py::test_requirements_txt_contains_runtime_and_test_dependencies
FAILED tests/unit/test_dependency_contract.py::test_requirements_dev_txt_is_only_a_compatibility_shim
```

**Step 3: Consolidate the dependency files**

Update `requirements.txt` to:

```text
# Runtime and contributor dependencies for Fesium
customtkinter>=5.0.0
pytest>=7.0.0
```

Update `requirements-dev.txt` to:

```text
-r requirements.txt
```

This keeps older contributor habits and existing commands from breaking, while making `requirements.txt` the real source of truth.

**Step 4: Update docs and workflow to use `requirements.txt` as primary**

Make these exact changes:

- In `README.md`, keep install commands on `requirements.txt` only
- In `CONTRIBUTING.md`, change setup to:

```bash
python -m pip install -r requirements.txt
```

Then add one sentence below it:

`requirements-dev.txt` is retained only as a compatibility shim and currently points back to `requirements.txt`.

- In `.github/workflows/python-tests.yml`, replace the two install lines with:

```yaml
          python -m pip install -r requirements.txt
```

**Step 5: Run the dependency contract and full unit suite**

Run:

```bash
python -m pytest tests/unit/test_dependency_contract.py -v
python -m pytest tests/unit -v
```

Expected output:

```text
3 passed
```

The full unit suite should remain green.

**Step 6: Commit**

```bash
git add requirements.txt requirements-dev.txt .github/workflows/python-tests.yml CONTRIBUTING.md README.md tests/unit/test_dependency_contract.py
git commit -m "chore: consolidate Fesium dependencies into requirements.txt"
```

## Task 6: Runtime App Icon Export and Window Wiring

**Files:**

- Create: `src/fesium/assets/icons/fesium-orbit-256.png`
- Create: `src/fesium/assets/icons/fesium-orbit.ico`
- Create: `src/fesium/ui/theme/window_icon.py`
- Modify: `src/fesium/ui/shell.py`
- Create: `tests/unit/ui/test_window_icon.py`

**Step 1: Write the failing icon tests**

Create `tests/unit/ui/test_window_icon.py`:

```python
from pathlib import Path

from fesium.ui.theme.window_icon import apply_window_icon, get_window_icon_paths


def test_get_window_icon_paths_point_to_expected_runtime_assets():
    paths = get_window_icon_paths()
    assert paths["png"].name == "fesium-orbit-256.png"
    assert paths["ico"].name == "fesium-orbit.ico"


def test_runtime_icon_files_exist():
    paths = get_window_icon_paths()
    assert Path(paths["png"]).exists()
    assert Path(paths["ico"]).exists()


def test_apply_window_icon_uses_png_asset(monkeypatch):
    fake_image = object()

    class FakeWindow:
        def __init__(self):
            self.iconphoto_args = None
            self.iconbitmap_args = None

        def iconphoto(self, *args):
            self.iconphoto_args = args

        def iconbitmap(self, **kwargs):
            self.iconbitmap_args = kwargs

    monkeypatch.setattr("fesium.ui.theme.window_icon.tk.PhotoImage", lambda file: fake_image)
    monkeypatch.setattr("fesium.ui.theme.window_icon.sys.platform", "linux")

    window = FakeWindow()
    assert apply_window_icon(window) is True
    assert window.iconphoto_args == (True, fake_image)
    assert window.iconbitmap_args is None
    assert window._fesium_icon_image is fake_image
```

**Step 2: Run the icon tests to verify they fail**

Run: `python -m pytest tests/unit/ui/test_window_icon.py -v`

Expected output:

```text
FAILED tests/unit/ui/test_window_icon.py::test_get_window_icon_paths_point_to_expected_runtime_assets - ModuleNotFoundError
```

**Step 3: Export the runtime icon assets from the master SVG**

Create `src/fesium/assets/icons/` and run:

```bash
magick -background none docs/assets/brand/fesium-orbit.svg -resize 256x256 src/fesium/assets/icons/fesium-orbit-256.png
magick -background none docs/assets/brand/fesium-orbit.svg -define icon:auto-resize=16,24,32,48,64,128,256 src/fesium/assets/icons/fesium-orbit.ico
```

**Step 4: Add a reusable window icon helper**

Create `src/fesium/ui/theme/window_icon.py`:

```python
import sys
import tkinter as tk
from pathlib import Path


ICON_DIR = Path(__file__).resolve().parents[2] / "assets" / "icons"


def get_window_icon_paths():
    return {
        "png": ICON_DIR / "fesium-orbit-256.png",
        "ico": ICON_DIR / "fesium-orbit.ico",
    }


def apply_window_icon(window) -> bool:
    paths = get_window_icon_paths()
    png_path = paths["png"]
    ico_path = paths["ico"]

    if not png_path.exists():
        return False

    image = tk.PhotoImage(file=str(png_path))
    window._fesium_icon_image = image
    window.iconphoto(True, image)

    if sys.platform == "win32" and ico_path.exists():
        try:
            window.iconbitmap(default=str(ico_path))
        except Exception:
            pass

    return True
```

Modify `src/fesium/ui/shell.py`:

```python
from fesium.ui.theme.window_icon import apply_window_icon
```

Then call this in `FesiumShell.__init__` after `self.configure(...)`:

```python
        apply_window_icon(self)
```

**Step 5: Run the icon tests and the full unit suite**

Run:

```bash
python -m pytest tests/unit/ui/test_window_icon.py -v
python -m pytest tests/unit -v
```

Expected output:

```text
tests/unit/ui/test_window_icon.py::test_get_window_icon_paths_point_to_expected_runtime_assets PASSED
tests/unit/ui/test_window_icon.py::test_runtime_icon_files_exist PASSED
tests/unit/ui/test_window_icon.py::test_apply_window_icon_uses_png_asset PASSED
```

The full unit suite should stay green.

**Step 6: Commit**

```bash
git add src/fesium/assets/icons src/fesium/ui/theme/window_icon.py src/fesium/ui/shell.py tests/unit/ui/test_window_icon.py
git commit -m "feat: add Fesium runtime window icon assets"
```

## Task 7: GitHub Metadata Rollout and Social Preview Upload

**Files:**

- No tracked file changes required

**Required reading:**

- GitHub Docs: `customizing-your-repositorys-social-media-preview`

**Step 1: Rename the GitHub repository**

Run:

```bash
gh repo rename Fesium --yes
```

Expected result:

- the repository slug becomes `goAuD/Fesium`
- the old slug redirects automatically

**Step 2: Update the local remote URL**

Run:

```bash
git remote set-url origin https://github.com/goAuD/Fesium.git
git remote -v
```

Expected output:

```text
origin  https://github.com/goAuD/Fesium.git (fetch)
origin  https://github.com/goAuD/Fesium.git (push)
```

**Step 3: Update About text and topics**

Run:

```bash
gh repo edit goAuD/Fesium -d "Offline-first local dev toolbox for students and developers." --add-topic offline-first --add-topic local-dev --add-topic developer-tools --add-topic desktop-app --add-topic python --add-topic customtkinter --add-topic php --add-topic sqlite --add-topic laravel --add-topic toolbox --remove-topic development-environment --remove-topic laravel-tool --remove-topic tkinter --remove-topic alternative-to-xampp
```

**Step 4: Verify the GitHub metadata**

Run:

```bash
gh repo view goAuD/Fesium --json name,nameWithOwner,description,homepageUrl,repositoryTopics
```

Expected output:

- `"name":"Fesium"`
- `"nameWithOwner":"goAuD/Fesium"`
- the exact approved description
- empty homepage
- the approved topic set

**Step 5: Upload the social preview image manually**

Use the GitHub web UI:

1. Open `https://github.com/goAuD/Fesium`
2. Go to `Settings`
3. In `Social preview`, click `Edit`
4. Upload `docs/assets/brand/fesium-social-preview.png`

Acceptance for the uploaded image:

- PNG format
- under 1 MB
- 1280x640
- visually matches the approved `Pure brand poster`

**Step 6: No git commit**

This task changes GitHub metadata and settings, not tracked files. Do not create an empty commit.

## Task 8: New Screenshot Asset and README Screenshot Section

**Files:**

- Create: `docs/assets/screenshots/fesium-overview.png`
- Create: `tests/unit/test_brand_screenshot.py`
- Modify: `README.md`

**Step 1: Write the failing screenshot contract**

Create `tests/unit/test_brand_screenshot.py`:

```python
import struct
from pathlib import Path


def read_png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(8)
        assert signature == b"\x89PNG\r\n\x1a\n"
        length = struct.unpack(">I", handle.read(4))[0]
        assert length == 13
        chunk = handle.read(4)
        assert chunk == b"IHDR"
        width = struct.unpack(">I", handle.read(4))[0]
        height = struct.unpack(">I", handle.read(4))[0]
        return width, height


def test_overview_screenshot_exists_and_is_large_enough():
    screenshot = Path("docs/assets/screenshots/fesium-overview.png")
    assert screenshot.exists()
    width, height = read_png_dimensions(screenshot)
    assert width >= 1000
    assert height >= 600


def test_readme_mentions_the_new_overview_screenshot():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "docs/assets/screenshots/fesium-overview.png" in readme
```

**Step 2: Run the screenshot test to verify it fails**

Run: `python -m pytest tests/unit/test_brand_screenshot.py -v`

Expected output:

```text
FAILED tests/unit/test_brand_screenshot.py::test_overview_screenshot_exists_and_is_large_enough
FAILED tests/unit/test_brand_screenshot.py::test_readme_mentions_the_new_overview_screenshot
```

**Step 3: Capture the screenshot**

1. Run the app:

```bash
python fesium.py
```

1. Switch to the `Overview` view.
2. Keep the window at the default `1280x860` size.
3. Capture a clean screenshot with no external clutter.
4. Save it exactly here:

```text
docs/assets/screenshots/fesium-overview.png
```

On Windows, use Snipping Tool or another lossless PNG capture tool.

**Step 4: Reference the screenshot in the README**

Add this section below `## Status` in `README.md`:

```markdown
## Overview

![Fesium Overview screenshot](docs/assets/screenshots/fesium-overview.png)
```

**Step 5: Run the screenshot test and a full regression**

Run:

```bash
python -m pytest tests/unit/test_brand_screenshot.py -v
python -m pytest tests/unit -v
```

Expected output:

```text
2 passed
```

The full unit suite should remain green.

**Step 6: Commit**

```bash
git add docs/assets/screenshots/fesium-overview.png README.md tests/unit/test_brand_screenshot.py
git commit -m "docs: add Fesium overview screenshot"
```

## Task 9: Version Bump, Changelog Finalization, and Release Tag

**Files:**

- Modify: `pyproject.toml`
- Modify: `src/fesium/__init__.py`
- Modify: `tests/unit/test_app_metadata.py`
- Modify: `CHANGELOG.md`

**Step 1: Write the failing version contract**

Append this test to `tests/unit/test_app_metadata.py`:

```python
def test_release_version_targets_v2():
    assert __version__ == "2.0.0"
```

**Step 2: Run the app metadata tests to verify they fail**

Run: `python -m pytest tests/unit/test_app_metadata.py -v`

Expected output:

```text
FAILED tests/unit/test_app_metadata.py::test_release_version_targets_v2
```

**Step 3: Bump the project version**

Update `pyproject.toml`:

```toml
version = "2.0.0"
```

Update `src/fesium/__init__.py`:

```python
__version__ = "2.0.0"
```

Do not change the package name.

**Step 4: Finalize the changelog for the release**

In `CHANGELOG.md`:

1. Move the current `Unreleased` rollout content into:

```markdown
## [2.0.0] - 2026-04-18
```

1. Keep the grouped sections (`Added`, `Changed`, `Removed`)
2. Add a short release-scoped line under `Changed` noting:
   - rebrand from `NanoServer` to `Fesium`
   - public repo asset rollout
   - GitHub metadata refresh

3. Recreate an empty `## [Unreleased]` section above `2.0.0`

**Step 5: Run the app metadata tests and a full regression**

Run:

```bash
python -m pytest tests/unit/test_app_metadata.py -v
python -m pytest tests/unit -v
```

Expected output:

```text
3 passed
```

The full unit suite should remain green.

**Step 6: Commit**

```bash
git add pyproject.toml src/fesium/__init__.py tests/unit/test_app_metadata.py CHANGELOG.md
git commit -m "chore: prepare Fesium v2.0.0 release"
```

**Step 7: Create the tag and GitHub release**

Run:

```bash
git tag -a v2.0.0 -m "Fesium v2.0.0"
git push origin main --follow-tags
gh release create v2.0.0 --title "Fesium v2.0.0" --notes-file CHANGELOG.md
```

Expected result:

- tag `v2.0.0` exists locally and on GitHub
- GitHub release `Fesium v2.0.0` is published

If you prefer cleaner release notes, prepare a small temporary release note file from the `2.0.0` section instead of using the whole changelog.

## Task 10: Final Verification and Post-Session Local Folder Rename

**Files:**

- No required tracked file changes

**Step 1: Run the full test suite**

Run:

```bash
python -m pytest -v
```

Expected output:

```text
... PASSED
=== X passed in Ys ===
```

There must be zero failures.

**Step 2: Run a compile check**

Run:

```bash
python -m compileall src
```

Expected output should list `src/fesium/...` without errors.

**Step 3: Verify GitHub state**

Run:

```bash
gh repo view goAuD/Fesium --json name,nameWithOwner,description,repositoryTopics
gh release view v2.0.0
```

Expected result:

- repo is `goAuD/Fesium`
- description matches exactly
- approved topics are present
- release `v2.0.0` exists

**Step 4: Rename the local folder only after the session ends**

Do **not** do this while the coding session is still attached to `D:\GitHub\NanoServer`.

After the session is finished, from `D:\GitHub` run:

```powershell
Rename-Item -LiteralPath "D:\GitHub\NanoServer" -NewName "Fesium"
```

Then reopen the project from:

```text
D:\GitHub\Fesium
```

**Step 5: Optional final commit**

If the screenshot task or README changes introduced anything uncommitted, commit them before ending. Otherwise there is no extra commit for the folder rename because it is outside git.
