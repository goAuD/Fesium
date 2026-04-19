from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from typing import Callable


class StaticServer:
    def __init__(self, on_log: Callable[[str], None] | None = None):
        self.on_log = on_log or (lambda message: None)
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self.port: int | None = None
        self.document_root: Path | None = None

    @property
    def is_running(self) -> bool:
        return self._httpd is not None

    def start(self, document_root: Path, port: int) -> str:
        root = Path(document_root)
        if self.is_running:
            raise RuntimeError("Static server is already running")
        if not root.exists():
            raise FileNotFoundError(f"Document root does not exist: {root}")
        if not root.is_dir():
            raise NotADirectoryError(f"Document root is not a directory: {root}")

        handler = partial(SimpleHTTPRequestHandler, directory=str(root))
        self._httpd = ThreadingHTTPServer(("localhost", port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self.port = port
        self.document_root = root
        url = f"http://localhost:{port}"
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
        self.on_log("[Fesium] Static server stopped")
