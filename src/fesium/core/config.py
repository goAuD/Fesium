import functools
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


def trace_execution(func):
    """Log function entry/exit with execution time."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug("-> Entering %s", func.__name__)
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.debug("<- Exiting %s (%.3fs)", func.__name__, elapsed)
            return result
        except Exception:
            logger.exception("Function %s failed", func.__name__)
            raise

    return wrapper


class Config:
    """Persist app settings in a JSON file, with legacy NanoServer fallback."""

    DEFAULT_CONFIG: Dict[str, Any] = {
        "last_project": "",
        "port": 8000,
        "window_geometry": "1280x860",
        "active_view": "overview",
    }

    def __init__(
        self,
        config_dir: Path,
        legacy_config_dir: Optional[Path] = None,
    ):
        self.config_dir = Path(config_dir)
        self.legacy_config_dir = Path(legacy_config_dir) if legacy_config_dir else None
        self.config_file = self.config_dir / "config.json"
        self._data = self.DEFAULT_CONFIG.copy()

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.load()

    def _resolve_load_source(self) -> Optional[Path]:
        if self.config_file.exists():
            return self.config_file

        if self.legacy_config_dir:
            legacy_file = self.legacy_config_dir / "config.json"
            if legacy_file.exists():
                return legacy_file

        return None

    @trace_execution
    def load(self) -> Dict[str, Any]:
        source = self._resolve_load_source()
        if source is None:
            return self._data

        try:
            loaded = json.loads(source.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load config from %s: %s", source, exc)
            self._data = self.DEFAULT_CONFIG.copy()
            return self._data

        self._data = {**self.DEFAULT_CONFIG, **loaded}
        return self._data

    @trace_execution
    def save(self) -> bool:
        try:
            self.config_file.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            return True
        except OSError as exc:
            logger.error("Failed to save config to %s: %s", self.config_file, exc)
            return False

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self.save()

    @property
    def last_project(self) -> str:
        return self._data.get("last_project", "")

    @last_project.setter
    def last_project(self, value: str) -> None:
        self.set("last_project", value)

    @property
    def port(self) -> int:
        return self._data.get("port", 8000)

    @port.setter
    def port(self, value: int) -> None:
        self.set("port", value)

    @property
    def active_view(self) -> str:
        return self._data.get("active_view", "overview")

    @active_view.setter
    def active_view(self, value: str) -> None:
        self.set("active_view", value)
