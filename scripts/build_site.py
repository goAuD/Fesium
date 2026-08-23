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
header.top nav a{{color:var(--muted); white-space:nowrap}}
header.top nav a:hover{{color:var(--ink); text-decoration:none}}

.hero{{padding:76px 0 60px; border-bottom:1px solid var(--border-soft)}}
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
}}

/* The five section anchors want 421px of their own and a 390px phone leaves
   about 240px for them, so every link was wrapping inside itself - three lines
   for "How it is built", one for "GitHub", which is what made the row look
   ragged rather than merely tight. Below this width the anchors go. The GitHub
   link stays because it is the only one that does something rather than
   scrolling to a section a reader will reach anyway. */
@media(max-width:680px){{
  header.top nav a.section{{display:none}}
  header.top nav{{gap:0}}
  .hero{{padding:56px 0 48px}}
  /* Edge to edge on a phone. 48px is exactly the wrap's two paddings, so this
     reaches both screen edges and no further - a screenshot of a desktop app
     needs every pixel it can get. */
  .shots{{width:calc(100% + 48px); margin-left:-24px}}
  .shot{{padding:8px; border-left:0; border-right:0}}
}}
@media(max-width:560px){{
  .bento{{grid-template-columns:1fr}}
  .span2,.span3,.span4,.span6{{grid-column:span 1}}
}}

/* Only once there is demonstrably room. At 1360px the column is 1072px wide
   and centred, leaving 144px on each side, so 100px of bleed clears the edge
   by a comfortable margin even with a scrollbar taken out. Below that the
   screenshots stay flush with the text rather than crowding it. */
@media(min-width:1360px){{
  .shots{{width:calc(100% + 200px); margin-left:-100px}}
}}

.shots{{
  display:grid; gap:var(--gutter); margin-top:38px;
  /* Sized against the column it sits in, never against the viewport.
     100vw counts the scrollbar and the layout does not, so anything measured
     that way is a scrollbar's width too wide - which is what pushed these off
     the right edge on a desktop window.

     26px is the figure's own padding plus its border, so this cancels exactly
     that and the picture lines up with the paragraphs above and below it. It
     always fits: the wrap keeps 24px of padding on each side. */
  width:calc(100% + 26px);
  margin-left:-13px;
}}
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
        tile("span3", "Serving", "<p>Pick a folder. Fesium looks at what is in it and works "
             "out how to serve it - PHP if the project uses PHP, the built-in static server "
             "if it's plain HTML, CSS and JavaScript. There's nothing to configure.</p>",
             metric="One folder, one click"),
        tile("span3", "Database", "<p>Browse the tables, columns and keys in your project's "
             "SQLite file, or any file you point it at, and run a statement when you need "
             "one. <strong>Read-only is on every time it starts.</strong> You can turn it "
             "off, but only for that session, so a DELETE you didn't mean has to be "
             "deliberate.</p>",
             metric="Read-only by default"),
        tile("span4", "Diagnostics", "<p>Fesium serves your site. It does not run a "
             "database. A Laravel project pointed at MySQL would start up fine and then "
             "fall over on its first query, somewhere four layers inside the framework "
             "where the message stops meaning anything. Fesium reads the project's "
             "<code>.env</code>, checks whether anything's listening at the address it "
             "asks for, and tells you <em>before</em> you open the site. It reads the host, "
             "the port and the database name. <strong>It never touches the "
             "password.</strong></p>",
             meta="before it breaks"),
        tile("span2", "Offline", "<p>No account, no telemetry, no CDN. The fonts and icons "
             "ship inside the package, so nothing is fetched while it runs. Which is the "
             "point, on a machine where installing things is the hard part.</p>",
             metric="Zero network"),
    ])

    engineering = "".join([
        tile("span2", "Selecting a project", "<p>Every click was spawning "
             "<code>php -v</code>, and eleven different handlers rebuild the views. A "
             "profiler found it. 78 milliseconds is too small to catch by eye and too big "
             "to leave alone.</p>",
             metric="78.6ms &rarr; 1.7ms"),
        tile("span2", "Starting a server", "<p>The port check was connecting to the port "
             "instead of trying to bind it, with no timeout set. Binding is the question "
             "the callers were really asking, and it answers in a fifth of a "
             "millisecond.</p>",
             metric="2047ms &rarr; 0.2ms"),
        tile("span2", "Contrast", "<p>Every button and every piece of text on every surface "
             "clears WCAG AA. A test checks the whole palette, so it stays that way.</p>",
             metric="AA, enforced"),
        tile("span6", "Tests that cannot see the screen",
             "<p>The unit tests run headless - no display, no PHP, no network. That makes "
             "them quick and portable, and completely blind to a panel that clips its own "
             "text. So there's a second tool: <code>scripts/check_layout.py</code> opens "
             "the real views in a real window and measures legibility, settling and tile "
             "balance. It has caught two regressions that every unit test was perfectly "
             "happy with.</p><p>It also produced the rule the rest of the suite follows "
             "now: <strong>if a check has never failed, it hasn't been tested</strong>. "
             "New assertions get run against the broken code first, to watch them "
             "fail.</p>"),
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
      <a class="section" href="#what">What it does</a>
      <a class="section" href="#who">Who it is for</a>
      <a class="section" href="#built">How it is built</a>
      <a class="section" href="#get">Get it</a>
      <a href="{REPO_URL}">GitHub</a>
    </nav>
  </div>
</header>

<div class="hero">
  <div class="wrap">
      <p class="eyebrow">Offline-first desktop app</p>
      <h1>Run your site. Read your database. Find out what is missing.</h1>
      <p>It started because a webdev teacher couldn't hand out Laragon licence keys and the
      assignment still needed a local PHP server. It's grown a fair way past that. Who it's
      for hasn't changed: someone on a machine they can't install much on, staring at an
      error thrown four frameworks deep, still learning which half of it matters.</p>
      <div class="cta">
        <a class="btn btn-primary" href="#get">Get started</a>
        <a class="btn btn-secondary" href="{REPO_URL}">View the source</a>
      </div>
  </div>
</div>

<section id="what">
  <div class="wrap">
    <h2>What it does</h2>
    <p class="lead">A local server and a database viewer. Both try to tell you what's going
    on instead of leaving you to work it out.</p>
    <div class="bento">{capabilities}</div>
  </div>
</section>

<section id="screens">
  <div class="wrap">
    <h2>What it looks like</h2>
    <p class="lead">Every view is a bento grid: the bigger the panel, the more it matters.
    These are captured straight from the running app by a script. The first attempt used a
    snipping tool, which shifted every colour channel by about +17 and washed the whole
    palette out.</p>
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
    <p class="lead">Most developer tools assume you already know. That's a fair assumption
    about most of their users, and it leaves a gap. Fesium aims at the gap, and treats it as
    an accessibility problem rather than something a better README would fix.</p>
    <p class="lead">Claims like that are cheap, so here's one place it changed a decision.
    Five typefaces were measured on how far apart they keep the characters beginners
    confuse, at the size the app actually sets them:</p>
    <div class="scroller">
    <table>
      <thead><tr><th scope="col">Typeface</th><th scope="col">Mean separation</th>
      <th scope="col">Worst pair</th><th scope="col">Score</th></tr></thead>
      <tbody>{typeface_rows}</tbody>
    </table>
    </div>
    <p class="lead">The column that decides it is the worst pair. Nobody misreads an
    average; you misread the one pair a face gets wrong. Source Sans 3 has the best mean
    here and still fails on it, and so did the heading face Fesium used before -
    <code>l</code> and <code>1</code> sat 0.10 apart, on a scale where 1.00 means the shapes
    have nothing in common.</p>
    <p class="lead">Fesium is set in <strong>Atkinson Hyperlegible</strong>. The Braille
    Institute drew it for exactly this, and it was the only candidate with a dotted zero.
    These screens are mostly ports, process ids, row counts and file paths, so the zero
    earns its keep.</p>
  </div>
</section>

<section id="built">
  <div class="wrap">
    <h2>How it is held together</h2>
    <p class="lead">Most of the work went into things a feature list cannot show. A few of
    them, with the numbers that came out.</p>
    <div class="bento">{engineering}</div>
  </div>
</section>

<section id="get">
  <div class="wrap">
    <h2>Get it</h2>
    <p class="lead">You'll need Python 3.10 or newer. PHP only if your project uses it -
    plain HTML, CSS and JavaScript works without.</p>
<pre><code><span class="c"># run it from a clone</span>
git clone {REPO_URL}.git
cd Fesium
python -m pip install -r requirements.txt
python fesium.py

<span class="c"># or install it and get a command</span>
python -m pip install -e .
fesium</code></pre>
    <p class="lead">Fesium serves your site. It doesn't run a database server, so if your
    project points at MySQL or PostgreSQL you'll need that running separately - Diagnostics
    will say so before you open the site. SQLite is a file, so it needs nothing.</p>
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
