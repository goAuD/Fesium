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
from typing import Callable, Dict, Optional

from fesium.core.config import trace_execution


logger = logging.getLogger(__name__)

IS_WINDOWS = sys.platform == "win32"


def get_subprocess_flags() -> Dict[str, object]:
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

    Thin shim over ``fesium.core.environment.detect_php`` — the authoritative
    PHP probe with a subprocess timeout. Kept as a boolean helper for call
    sites that only need availability.
    """
    from fesium.core.environment import detect_php

    return detect_php().php_available


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("localhost", port)) == 0


def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> Optional[int]:
    """Find an available port starting from start_port."""
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
        self._log_thread: Optional[threading.Thread] = None
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
        command = ["php", "-S", f"localhost:{port}", "-t", document_root]

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

            logger.info("Server started at http://localhost:%s", port)
            self.on_log(f"[Fesium] Started at http://localhost:{port}")
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
        return f"http://localhost:{self.port}"
