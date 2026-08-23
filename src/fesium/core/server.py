"""
Fesium - Server Module
Handles PHP built-in server management.
Cross-platform compatible (Windows/Linux/macOS).
"""

import logging
import os
import socket
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path

from fesium.core.config import trace_execution

logger = logging.getLogger(__name__)

IS_WINDOWS = sys.platform == "win32"


def get_subprocess_flags() -> dict[str, object]:
    """Get platform-specific subprocess flags."""
    if IS_WINDOWS:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return {
            "startupinfo": startupinfo,
            "creationflags": subprocess.CREATE_NO_WINDOW,
        }
    return {}


@trace_execution
def check_php_installed() -> bool:
    """Check if PHP is available in PATH.

    Thin shim over ``fesium.core.environment.detect_php`` - the authoritative
    PHP probe with a subprocess timeout. Kept as a boolean helper for call
    sites that only need availability.
    """
    from fesium.core.environment import detect_php

    return detect_php().php_available


# Bind and connect on the same literal address, never on the name.
#
# "localhost" resolves to ::1 before 127.0.0.1 on Windows and macOS, and both
# servers bind IPv4 only. A client that goes by name therefore tries IPv6
# first, against a port nothing is listening on. Measured on Windows that
# costs 2131ms against 2ms to the literal address - and on a macOS CI runner
# the IPv6 attempt does not refuse at all, it hangs, which is what left a
# test job running until GitHub's six hour limit.
LOOPBACK = "127.0.0.1"

# The PHP built-in server serves the document root raw - .env and .git/config
# included, with none of the checks ProjectFileHandler applies on the Python
# side. This router restores the same filter: dot-paths get a 403, everything
# else returns false and falls through to the built-in handler.
PHP_ROUTER = Path(__file__).resolve().parents[1] / "assets" / "php" / "router.php"


def is_port_in_use(port: int, host: str = LOOPBACK) -> bool:
    """Can a local server take this port?

    Asked by trying to bind it, not by trying to connect to it. Every caller
    here is about to bind - PHPServer and StaticServer both check before they
    start, and find_available_port exists to pick one they can have - and
    "can I bind this" is simply a different question from "is something
    answering here". A connect test gets both directions wrong: a port bound
    on another interface looks free, and on Windows, whose dynamic range
    covers everything from 1024 up, the answer depends on whatever the machine
    happens to be doing. That made the port-scan test fail intermittently on
    CI while every other runner passed.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
        except OSError:
            return True
        return False


def wait_until_serving(port: int, *, timeout: float = 15.0, host: str = LOOPBACK) -> bool:
    """Block until something answers on ``port``, or give up.

    Connecting, not binding - the opposite of :func:`is_port_in_use`, and for
    the opposite reason. That function asks "may I have this port", which only
    a bind can answer. This one asks "is the server I just spawned ready to be
    used", which only a connect can answer.

    ``php -S`` is a subprocess, so ``Popen`` returning does not mean PHP has
    bound anything yet. Without this the app reported "Started", enabled Open
    in Browser, and handed the user a connection error if they were quick -
    and reported success just the same when PHP never came up at all.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.05)
    return False


def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int | None:
    """First bindable port at or above ``start_port``, or None if there is none.

    The answer can go stale between here and the bind that follows; nothing
    can close that window, and the callers already handle a failed start.
    """
    for offset in range(max_attempts):
        port = start_port + offset
        if not is_port_in_use(port):
            return port
    return None


class PHPServer:
    """Manage the PHP built-in development server and capture log output."""

    def __init__(self, on_log: Callable[[str], None] = None):
        self.process = None
        self.is_running = False
        self.port = 8000
        self.document_root = os.getcwd()
        self.last_error = ""
        self.on_log = on_log or (lambda message: None)
        self._log_thread: threading.Thread | None = None
        self._stop_logging = threading.Event()

    @trace_execution
    def start(self, document_root: str, port: int = 8000) -> bool:
        """Start the PHP development server."""
        if self.is_running:
            logger.warning("Server already running")
            self.last_error = "Server already running"
            return False

        if not os.path.isdir(document_root):
            error_message = f"Document root does not exist: {document_root}"
            logger.error(error_message)
            self.last_error = error_message
            self.on_log(f"[Fesium] ERROR: {error_message}")
            return False

        if is_port_in_use(port):
            available_port = find_available_port(port)
            if available_port is None:
                self.last_error = f"Ports {port}-{port + 9} are all in use"
                logger.error(self.last_error)
                self.on_log(f"[Fesium] ERROR: {self.last_error}")
                return False
            logger.info("Port %s busy, using %s", port, available_port)
            self.on_log(f"[Fesium] Port {port} busy, using {available_port}")
            port = available_port

        self.port = port
        self.document_root = document_root
        command = ["php", "-S", f"{LOOPBACK}:{port}", "-t", document_root, str(PHP_ROUTER)]

        try:
            self.last_error = ""
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                **get_subprocess_flags(),
            )
            self.is_running = True
            self._stop_logging.clear()
            self._log_thread = threading.Thread(target=self._capture_logs, daemon=True)
            self._log_thread.start()

            if not wait_until_serving(port):
                self.stop()
                self.last_error = (
                    f"PHP did not start listening on port {port}. "
                    "Check the log above for what it printed.")
                logger.error(self.last_error)
                self.on_log(f"[Fesium] ERROR: {self.last_error}")
                return False

            logger.info("Server started at http://%s:%s", LOOPBACK, port)
            self.on_log(f"[Fesium] Started at http://{LOOPBACK}:{port}")
            self.on_log(f"[Fesium] Document root: {document_root}")
            return True
        except FileNotFoundError:
            logger.error("PHP not found - cannot start server")
            self.last_error = "PHP not found - cannot start server"
            return False
        except Exception as exc:
            logger.error("Failed to start server: %s", exc)
            self.last_error = str(exc) or exc.__class__.__name__
            return False

    def _capture_logs(self) -> None:
        """Background thread to capture PHP server output."""
        try:
            while not self._stop_logging.is_set() and self.process:
                line = self.process.stdout.readline()
                if line:
                    line = line.rstrip()
                    logger.debug("PHP: %s", line)
                    self.on_log(line)
                elif self.process.poll() is not None:
                    break
        except Exception as exc:
            logger.error("Log capture error: %s", exc)

    @trace_execution
    def stop(self) -> None:
        """Stop the PHP server."""
        self._stop_logging.set()

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            finally:
                self.process = None

        self.is_running = False
        self.last_error = ""
        logger.info("Server stopped")
        self.on_log("[Fesium] Server stopped")

    def restart(self) -> bool:
        """Restart the server with the same settings."""
        document_root = self.document_root
        port = self.port
        self.stop()
        return self.start(document_root, port)

    @property
    def url(self) -> str:
        """Get the server URL."""
        return f"http://{LOOPBACK}:{self.port}"
