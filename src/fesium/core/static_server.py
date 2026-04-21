from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from typing import Callable

from fesium.core.server import find_available_port, is_port_in_use


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

    def start(self, document_root: Path, port: int) -> str:
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

        handler = partial(SimpleHTTPRequestHandler, directory=str(root))
        self._httpd = ThreadingHTTPServer(("localhost", port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self.port = port
        self.document_root = root
        self.last_error = ""
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
        self.last_error = ""
        self.on_log("[Fesium] Static server stopped")
