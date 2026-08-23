import html
import threading
import urllib.parse
from collections.abc import Callable, Iterable
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path

from fesium.core.server import LOOPBACK, find_available_port, is_port_in_use

# Straight from the app's own palette, so the page a browser lands on looks
# like the app that served it.
_GROUND, _PANEL, _BORDER = "#121419", "#181d25", "#2b3440"
_INK, _MUTED, _ACCENT = "#eef3f7", "#8f9aa8", "#5DA9B3"


def _fully_unquote(text: str) -> str:
    """Decode percent-escapes until the string stops changing.

    One pass is not enough: this check runs before ``translate_path``, which
    unquotes again on its own. A single decode let ``/%252Eenv`` through as
    ``%2Eenv`` - not a dot segment here, but ``.env`` by the time the stdlib
    opened the file. Decoding to a fixed point means both layers see the same
    path. Each pass that changes anything shortens the string, so this ends.
    """
    decoded = urllib.parse.unquote(text)
    while decoded != text:
        text = decoded
        decoded = urllib.parse.unquote(text)
    return decoded


def is_hidden_path(request_path: str) -> bool:
    """Does this request reach for a dot-file or a dot-directory?

    ``SimpleHTTPRequestHandler`` serves the document root as it finds it, which
    for a project folder means ``.env`` and the whole of ``.git`` are available
    over HTTP. Localhost only, but Fesium reads four keys out of a project's
    ``.env`` and deliberately never touches the credentials in it - serving the
    file whole rather undoes that care.

    Segments are checked after unquoting to a fixed point, so ``%2Eenv`` and
    its double-encoded form ``%252Eenv`` are both the same request as ``.env``.
    """
    path = _fully_unquote(urllib.parse.urlsplit(request_path).path)
    return any(segment.startswith(".") for segment in path.replace("\\", "/").split("/") if segment)


def render_no_index_page(directory: str, hints: Iterable[str] = ()) -> bytes:
    """The page shown where a directory listing used to be.

    A listing of a source repository looks like a broken website, and says
    nothing about why it is broken. This says what is missing and, when the
    project is one Fesium recognises, which command produces something to
    serve.
    """
    advice = "".join(f"<li>{html.escape(line)}</li>" for line in hints)
    advice_block = f"<ul>{advice}</ul>" if advice else (
        "<p>Fesium serves the files in this folder. It needs an "
        "<code>index.html</code> here to have something to show.</p>")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nothing to serve here - Fesium</title>
<style>
 body{{margin:0;background:{_GROUND};color:{_INK};font:16px/1.65 system-ui,sans-serif;
   display:flex;min-height:100vh;align-items:center;justify-content:center;padding:24px}}
 main{{max-width:60ch;border:1px solid {_BORDER};background:{_PANEL};padding:32px}}
 h1{{margin:0 0 6px;font-size:23px}}
 p,li{{color:{_MUTED}}} p{{margin:14px 0 0}}
 ul{{margin:14px 0 0;padding-left:20px}} li{{margin:9px 0}}
 code{{color:{_ACCENT};font-family:ui-monospace,monospace;font-size:.9em}}
 .where{{margin-top:22px;padding-top:16px;border-top:1px solid {_BORDER};font-size:14px}}
</style></head><body><main>
<h1>Nothing to serve here</h1>
<p>There is no <code>index.html</code> in this folder, so there is no page to open.</p>
{advice_block}
<p class="where">Serving <code>{html.escape(directory)}</code> - Fesium</p>
</main></body></html>
""".encode()


class ProjectFileHandler(SimpleHTTPRequestHandler):
    """Serves a project folder without handing out its secrets or its tree."""

    def __init__(self, *args, hints: Iterable[str] = (), **kwargs):
        # Set before super().__init__, which handles the request inline.
        self._hints = tuple(hints)
        super().__init__(*args, **kwargs)

    def send_head(self):
        if is_hidden_path(self.path):
            self.send_error(HTTPStatus.FORBIDDEN, "Not served")
            return None
        return super().send_head()

    def list_directory(self, path):
        """Replace the file listing with something that explains itself."""
        body = render_no_index_page(self.path, self._hints)
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        return BytesIO(body)

    def log_message(self, format, *args):  # noqa: A002 - the base class names it
        """Route request logs into the app instead of stderr."""
        sink = getattr(self.server, "fesium_log", None)
        if sink is not None:
            sink(f"[{self.address_string()}] {format % args}")


class StaticServer:
    def __init__(self, on_log: Callable[[str], None] | None = None):
        self.on_log = on_log or (lambda message: None)
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.port: int | None = None
        self.document_root: Path | None = None
        self.last_error = ""

    @property
    def is_running(self) -> bool:
        return self._httpd is not None

    def start(self, document_root: Path, port: int, *, hints: Iterable[str] = ()) -> str:
        root = Path(document_root)
        if self.is_running:
            self.last_error = "Static server is already running"
            raise RuntimeError("Static server is already running")
        if not root.exists():
            self.last_error = f"Document root does not exist: {root}"
            raise FileNotFoundError(f"Document root does not exist: {root}")
        if not root.is_dir():
            self.last_error = f"Document root is not a directory: {root}"
            raise NotADirectoryError(f"Document root is not a directory: {root}")
        if is_port_in_use(port):
            available_port = find_available_port(port)
            if available_port is None:
                self.last_error = f"Ports {port}-{port + 9} are all in use"
                raise OSError(self.last_error)
            self.on_log(f"[Fesium] Port {port} busy, using {available_port}")
            port = available_port

        handler = partial(ProjectFileHandler, directory=str(root), hints=tuple(hints))
        self._httpd = ThreadingHTTPServer((LOOPBACK, port), handler)
        self._httpd.fesium_log = self.on_log
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self.port = port
        self.document_root = root
        self.last_error = ""
        url = f"http://{LOOPBACK}:{port}"
        self.on_log(f"[Fesium] Started static server at {url}")
        return url

    def stop(self) -> None:
        if self._httpd is None:
            return

        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=5)
        self._httpd = None
        self._thread = None
        self.port = None
        self.document_root = None
        self.last_error = ""
        self.on_log("[Fesium] Static server stopped")
