"""Build the GitHub Pages site into ``site/``.

Authoring-time only, like build_icons.py and build_brand.py. The generated file
is committed, so the workflow only has to upload it, and a test fails if the two
disagree. Needs nothing beyond the standard library:

    python scripts/build_site.py

Two decisions worth stating.

**The page is one self-contained file.** The screenshots and the mark are
inlined as data URIs rather than copied into ``site/assets/``. A copy step is
a drift risk - the copies would go stale the next time the screenshots are
regenerated - and at this size the whole page is smaller than a single stock
photograph. The one exception is the social preview, because Open Graph needs
an absolute URL to a real file.

**The palette and the type come from the app, not from a stylesheet written
here.** COLOR_TOKENS is imported, so the site cannot drift from the product it
is describing. That already happened once to the brand assets.
"""

import base64
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fesium._version import __version__  # noqa: E402
from fesium.ui.theme.tokens import COLOR_TOKENS  # noqa: E402

SITE = ROOT / "site"
SCREENSHOTS = ROOT / "docs" / "assets" / "screenshots"
BRAND = ROOT / "docs" / "assets" / "brand"
PAGES_URL = "https://goaud.github.io/Fesium"
REPO_URL = "https://github.com/goAuD/Fesium"


def data_uri(path: Path) -> str:
    kind = "svg+xml" if path.suffix == ".svg" else path.suffix.lstrip(".")
    return f"data:image/{kind};base64," + base64.b64encode(path.read_bytes()).decode()


def tile(span: str, title: str, body: str, *, metric: str = "", meta: str = "") -> str:
    """One bento tile, built the way the app builds one.

    Title small and quiet, size carrying the hierarchy, and the accent kept for
    the figure that the tile is actually about.
    """
    head = f'<h3>{title}</h3>' + (f'<span class="meta">{meta}</span>' if meta else "")
    figure = f'<p class="metric">{metric}</p>' if metric else ""
    return f'<article class="tile {span}"><header>{head}</header>{figure}{body}</article>'


def build() -> str:
    c = COLOR_TOKENS
    css = f"""
:root{{
  --ground:{c['bg.app']}; --panel:{c['bg.panel']}; --panel-alt:{c['bg.panel_alt']};
  --hover:{c['bg.panel_hover']}; --sidebar:{c['bg.sidebar']};
  --border:{c['border.default']}; --border-soft:{c['border.soft']};
  --ink:{c['text.primary']}; --muted:{c['text.secondary']};
  --accent:{c['accent.primary']}; --accent-hover:{c['accent.primary_hover']};
  --accent-soft:{c['accent.primary_soft']};
  --ok:{c['accent.success']}; --warn:{c['accent.warning']}; --bad:{c['accent.danger']};
  --sans:"Atkinson Hyperlegible",system-ui,-apple-system,sans-serif;
  --mono:"JetBrains Mono",ui-monospace,SFMono-Regular,monospace;
  --gutter:16px;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
@media (prefers-reduced-motion:reduce){{html{{scroll-behavior:auto}}
  *{{animation:none!important;transition:none!important}}}}
body{{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:var(--sans); font-size:17px; line-height:1.65;
  -webkit-font-smoothing:antialiased;
}}
.wrap{{max-width:1120px; margin:0 auto; padding:0 24px}}
a{{color:var(--accent); text-decoration:none}}
a:hover{{color:var(--accent-hover); text-decoration:underline}}
a:focus-visible,button:focus-visible{{outline:2px solid var(--accent); outline-offset:3px}}
h1,h2,h3{{margin:0; text-wrap:balance; font-weight:700}}
code{{font-family:var(--mono); font-size:.86em}}

/* Square corners everywhere, because the app's SHAPE_TOKENS sets every
   structural radius to 0 and this page is describing that app. */
.tile,.shot,.btn,pre{{border-radius:0}}

header.top{{border-bottom:1px solid var(--border-soft); background:var(--sidebar)}}
header.top .wrap{{display:flex; align-items:center; gap:14px; height:64px}}
header.top img{{width:28px; height:28px; display:block}}
header.top .name{{font-weight:700; letter-spacing:-.01em}}
header.top nav{{margin-left:auto; display:flex; gap:22px; font-size:15px}}
header.top nav a{{color:var(--muted)}}
header.top nav a:hover{{color:var(--ink); text-decoration:none}}

.hero{{padding:88px 0 64px; border-bottom:1px solid var(--border-soft)}}
.hero-grid{{display:grid; grid-template-columns:minmax(0,1fr) auto; gap:56px; align-items:center}}
.hero img{{width:168px; height:168px; display:block}}
.eyebrow{{
  font-size:13px; letter-spacing:.16em; text-transform:uppercase;
  color:var(--accent); margin:0 0 16px; font-weight:700;
}}
.hero h1{{font-size:clamp(38px,5.2vw,60px); line-height:1.08; letter-spacing:-.02em}}
.hero p{{color:var(--muted); font-size:19px; max-width:56ch; margin:22px 0 0}}
.cta{{display:flex; gap:12px; margin-top:32px; flex-wrap:wrap}}
.btn{{
  display:inline-block; padding:13px 24px; font-weight:700; font-size:16px;
  border:1px solid var(--accent); font-family:var(--sans);
}}
.btn-primary{{background:var(--accent); color:{c['bg.app']}}}
.btn-primary:hover{{background:var(--accent-hover); color:{c['bg.app']}; text-decoration:none}}
.btn-secondary{{color:var(--accent); background:transparent}}
.btn-secondary:hover{{background:var(--accent-soft); text-decoration:none}}

section{{padding:76px 0; border-bottom:1px solid var(--border-soft)}}
.lead{{color:var(--muted); max-width:64ch; margin:14px 0 0; font-size:18px}}
h2{{font-size:29px; letter-spacing:-.015em}}

.bento{{
  display:grid; grid-template-columns:repeat(6,1fr); gap:var(--gutter); margin-top:38px;
}}
.tile{{
  border:1px solid var(--border); background:var(--panel);
  padding:24px; display:flex; flex-direction:column; gap:12px; min-width:0;
}}
.tile header{{display:flex; align-items:baseline; gap:10px}}
.tile h3{{
  font-size:12px; letter-spacing:.13em; text-transform:uppercase;
  color:var(--muted); font-weight:700;
}}
.tile .meta{{margin-left:auto; font-family:var(--mono); font-size:12px; color:var(--muted)}}
.tile p{{margin:0; color:var(--muted); font-size:16px}}
.tile p.metric{{
  font-family:var(--mono); font-size:27px; font-weight:700; color:var(--ink);
  margin:0; font-variant-numeric:tabular-nums; line-height:1.15;
}}
.tile strong{{color:var(--ink); font-weight:700}}
.span2{{grid-column:span 2}} .span3{{grid-column:span 3}}
.span4{{grid-column:span 4}} .span6{{grid-column:span 6}}
@media(max-width:900px){{
  .bento{{grid-template-columns:repeat(2,1fr)}}
  .span3,.span4,.span6{{grid-column:span 2}}
  .hero-grid{{grid-template-columns:1fr}}
  .hero img{{width:120px; height:120px}}
}}
@media(max-width:560px){{
  .bento{{grid-template-columns:1fr}}
  .span2,.span3,.span4,.span6{{grid-column:span 1}}
}}

.shots{{display:grid; gap:var(--gutter); margin-top:38px}}
.shot{{border:1px solid var(--border); background:var(--panel-alt); padding:12px}}
.shot img{{width:100%; height:auto; display:block}}
.shot figcaption{{
  color:var(--muted); font-size:15px; padding:14px 4px 4px; margin:0;
}}

table{{border-collapse:collapse; width:100%; font-size:15px; margin-top:8px}}
th,td{{padding:9px 12px; text-align:right; border-bottom:1px solid var(--border-soft)}}
th:first-child,td:first-child{{text-align:left}}
th{{
  font-size:11px; letter-spacing:.11em; text-transform:uppercase;
  color:var(--muted); font-weight:700;
}}
td{{font-family:var(--mono); font-variant-numeric:tabular-nums; color:var(--muted)}}
td:first-child{{font-family:var(--sans)}}
tr.pick td{{color:var(--ink)}} tr.pick td.score{{color:var(--ok)}}
td.score.bad{{color:var(--bad)}}
.scroller{{overflow-x:auto}}

pre{{
  background:var(--panel-alt); border:1px solid var(--border); padding:18px 20px;
  overflow-x:auto; margin:22px 0 0;
}}
pre code{{font-size:14.5px; color:var(--ink); line-height:1.8}}
pre .c{{color:var(--muted)}}

footer{{padding:52px 0 72px; color:var(--muted); font-size:15px}}
footer .wrap{{display:flex; gap:28px; flex-wrap:wrap; align-items:center}}
footer nav{{margin-left:auto; display:flex; gap:22px; flex-wrap:wrap}}
"""

    mark = data_uri(BRAND / "fesium-orbit.svg")
    overview = data_uri(SCREENSHOTS / "fesium-overview.png")
    server = data_uri(SCREENSHOTS / "fesium-server.png")

    capabilities = "".join([
        tile("span3", "Serving", "<p>Point Fesium at a folder and it works out what the "
             "project is. A site that uses PHP gets PHP. A plain HTML, CSS and JavaScript "
             "site gets the built-in static server - <strong>not</strong> a PHP process it "
             "has no use for, which is what most tools hand it.</p>",
             metric="One folder, one click"),
        tile("span3", "Database", "<p>Browse the tables, columns and keys of the project's "
             "SQLite file, or any file you pick. Run one statement at a time. "
             "<strong>Read-only is on at every launch</strong> and write mode lasts only "
             "for the session, so a stray DELETE cannot happen by muscle memory.</p>",
             metric="Read-only by default"),
        tile("span4", "Diagnostics", "<p>Fesium serves your site. It does not run a "
             "database server - and a Laravel project pointed at MySQL used to start "
             "cleanly and then fail on its first query, with an error thrown from inside "
             "the framework where a student has no chance of reading it. Fesium now reads "
             "the project's <code>.env</code>, checks whether anything is actually "
             "listening where it asks, and says so in plain words <em>before</em> you open "
             "the site. It reads the host, the port and the database name. "
             "<strong>Never the credentials.</strong></p>",
             meta="before it breaks"),
        tile("span2", "Offline", "<p>No account, no telemetry, no CDN, nothing fetched at "
             "runtime. Fonts and icons are in the package. It works on a locked-down "
             "school machine, which is the machine it was written for.</p>",
             metric="Zero network"),
    ])

    engineering = "".join([
        tile("span2", "Selecting a project", "<p>Every UI action was spawning "
             "<code>php -v</code>, and eleven handlers rebuild the views, so each click "
             "stalled the window. Found by profiling, not by guessing.</p>",
             metric="78.6ms &rarr; 1.7ms"),
        tile("span2", "Starting a server", "<p>The port check connected to the port "
             "instead of trying to bind it, with no timeout. Binding answers the question "
             "the callers actually have.</p>",
             metric="2047ms &rarr; 0.2ms"),
        tile("span2", "Contrast", "<p>Every button and every text-on-surface pairing "
             "clears WCAG AA, and a test fails the build if one stops doing so.</p>",
             metric="AA, enforced"),
        tile("span6", "The suite cannot see a layout bug, so something else has to",
             "<p>The unit tests run headless, with no display, no PHP and no network - "
             "which makes them fast and portable, and completely blind to a panel that "
             "clips its own text. So there is a second instrument: "
             "<code>scripts/check_layout.py</code> drives the real views in a live window "
             "and measures legibility, settling and tile balance. It has caught two real "
             "regressions that every unit test happily passed. The rule that came out of "
             "it: <strong>a check that has never failed has not been tested</strong> - so "
             "every new assertion is proved against the broken code before it is "
             "trusted.</p>"),
    ])

    typeface_rows = "".join(
        f'<tr class="{cls}"><td>{name}</td><td>{mean}</td><td>{pair}</td>'
        f'<td class="score {bad}">{score}</td></tr>'
        for name, mean, pair, score, cls, bad in [
            ("Sora", "0.41", "l / 1", "0.10", "", "bad"),
            ("IBM Plex Sans", "0.52", "I / 1", "0.28", "", ""),
            ("Atkinson Hyperlegible", "0.51", "rn / m", "0.17", "pick", ""),
            ("Source Sans 3", "0.62", "I / l", "0.08", "", "bad"),
            ("Public Sans", "0.59", "I / l", "0.25", "", ""),
        ])

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Fesium - local dev tools for students and developers</title>
<meta name="description" content="An offline-first desktop app that serves your local site,
 reads your SQLite database, and tells you what is missing before it breaks. Built for
 people who are still learning.">
<meta name="theme-color" content="{c['bg.app']}">
<meta property="og:title" content="Fesium">
<meta property="og:description" content="Local dev tools for students and developers.
 Offline-first, read-only by default, and it explains what is wrong.">
<meta property="og:image" content="{PAGES_URL}/social-preview.png">
<meta property="og:url" content="{PAGES_URL}/">
<meta property="og:type" content="website">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{mark}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&amp;family=JetBrains+Mono:wght@400;700&amp;display=swap">
<style>{css}</style>
</head>
<body>

<header class="top">
  <div class="wrap">
    <img src="{mark}" alt="">
    <span class="name">Fesium</span>
    <nav>
      <a href="#what">What it does</a>
      <a href="#who">Who it is for</a>
      <a href="#built">How it is built</a>
      <a href="#get">Get it</a>
      <a href="{REPO_URL}">GitHub</a>
    </nav>
  </div>
</header>

<div class="hero">
  <div class="wrap hero-grid">
    <div>
      <p class="eyebrow">Offline-first desktop app</p>
      <h1>Run your site. Read your database. Find out what is missing.</h1>
      <p>Fesium started because a webdev teacher could not hand out a Laragon licence key
      and the assignment still needed a local PHP server. It is a long way past that now,
      but the audience has not changed: it is for the person whose machine is locked down,
      whose error message came from four frameworks deep, and who has not yet learned which
      half of it matters.</p>
      <div class="cta">
        <a class="btn btn-primary" href="#get">Get started</a>
        <a class="btn btn-secondary" href="{REPO_URL}">View the source</a>
      </div>
    </div>
    <img src="{mark}" alt="The Fesium mark: a tilted orbit and its nucleus cut out of a solid square">
  </div>
</div>

<section id="what">
  <div class="wrap">
    <h2>What it does</h2>
    <p class="lead">Four things, properly, instead of twenty things badly. It is a local
    server and a database viewer that explain themselves.</p>
    <div class="bento">{capabilities}</div>
  </div>
</section>

<section id="screens">
  <div class="wrap">
    <h2>What it looks like</h2>
    <p class="lead">Every view is a bento grid, so the size of a panel tells you how much it
    matters. Screenshots are captured from the running app by a script, not photographed -
    a snipping tool shifted every colour channel by about +17 and washed the palette out.</p>
    <div class="shots">
      <figure class="shot">
        <img src="{overview}" width="1276" height="816" loading="lazy"
             alt="Fesium's Overview: serving state with Start, Stop and Open in Browser,
                  alongside environment, workspace and a live activity log">
        <figcaption><strong>Overview</strong> - what is running, where, and what just
        happened, with the controls in the tile itself.</figcaption>
      </figure>
      <figure class="shot">
        <img src="{server}" width="1276" height="816" loading="lazy"
             alt="Fesium's Server view: runtime facts in a compact two-column list
                  beside a full-height live log">
        <figcaption><strong>Server</strong> - the runtime facts stay compact so the live log
        gets the room.</figcaption>
      </figure>
    </div>
  </div>
</section>

<section id="who">
  <div class="wrap">
    <h2>Built for people who are still learning</h2>
    <p class="lead">Most developer tools are written for people who already know. That is a
    reasonable choice and it leaves a real gap. Fesium aims at the gap - and treats it as an
    accessibility problem, not a documentation one.</p>
    <p class="lead">It is easy to put that on a page and never let it decide anything, so
    here is a decision it actually made. The app's typeface was chosen by measuring how far
    apart five faces keep the characters a beginner confuses, at the size the app sets them:</p>
    <div class="scroller">
    <table>
      <thead><tr><th scope="col">Typeface</th><th scope="col">Mean separation</th>
      <th scope="col">Worst pair</th><th scope="col">Score</th></tr></thead>
      <tbody>{typeface_rows}</tbody>
    </table>
    </div>
    <p class="lead">Read the worst pair, not the average: a reader is not tripped by a mean,
    they are tripped by the one pair a face gets wrong. Source Sans 3 takes the best average
    and is still disqualified by a single column, and the previous heading face put
    <code>l</code> and <code>1</code> 0.10 apart on a scale where 1.00 means the two shapes
    share nothing.</p>
    <p class="lead">Fesium is set in <strong>Atkinson Hyperlegible</strong>, drawn by the
    Braille Institute for exactly this, and the only candidate with a dotted zero. On a
    screen made of ports, process ids, row counts and file paths, the zero is the character
    that costs the most when it is misread.</p>
  </div>
</section>

<section id="built">
  <div class="wrap">
    <h2>How it is held together</h2>
    <p class="lead">It is a portfolio piece, so the interesting part is not the feature list.
    It is what happens when a claim cannot be checked.</p>
    <div class="bento">{engineering}</div>
  </div>
</section>

<section id="get">
  <div class="wrap">
    <h2>Get it</h2>
    <p class="lead">Python 3.10 or newer. PHP only if your project actually uses PHP - a
    plain HTML, CSS and JavaScript project is served either way.</p>
<pre><code><span class="c"># run it from a clone</span>
git clone {REPO_URL}.git
cd Fesium
python -m pip install -r requirements.txt
python fesium.py

<span class="c"># or install it and get a command</span>
python -m pip install -e .
fesium</code></pre>
    <p class="lead">Fesium serves your site; it does not run a database server. A project
    pointed at MySQL or PostgreSQL needs that service running separately, and Diagnostics
    tells you so before you open the site. SQLite needs nothing at all, because it is a
    file.</p>
    <div class="cta">
      <a class="btn btn-primary" href="{REPO_URL}/releases/latest">Download v{__version__}</a>
      <a class="btn btn-secondary" href="{REPO_URL}/blob/main/docs/dev/setup.md">Setup guide</a>
    </div>
  </div>
</section>

<footer>
  <div class="wrap">
    <span>Fesium v{__version__} - Apache License 2.0</span>
    <nav>
      <a href="{REPO_URL}">Source</a>
      <a href="{REPO_URL}/releases">Releases</a>
      <a href="{REPO_URL}/blob/main/CHANGELOG.md">Changelog</a>
      <a href="{REPO_URL}/blob/main/ROADMAP.md">Roadmap</a>
    </nav>
  </div>
</footer>

</body>
</html>
"""


def main() -> int:
    for required in (SCREENSHOTS / "fesium-overview.png", SCREENSHOTS / "fesium-server.png",
                     BRAND / "fesium-orbit.svg", BRAND / "fesium-social-preview.png"):
        if not required.exists():
            print(f"missing {required.relative_to(ROOT)}", file=sys.stderr)
            return 1

    SITE.mkdir(exist_ok=True)
    page = SITE / "index.html"
    page.write_text(build(), encoding="utf-8")
    # Open Graph needs a real file at an absolute URL, so this one is copied
    # rather than inlined.
    shutil.copy(BRAND / "fesium-social-preview.png", SITE / "social-preview.png")
    # Pages runs Jekyll unless told not to, which would try to process this.
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    for produced in (page, SITE / "social-preview.png"):
        print(f"{produced.relative_to(ROOT)!s:<34} {produced.stat().st_size:>8d} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
