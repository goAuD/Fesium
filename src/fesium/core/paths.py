from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    home_dir: Path

    @property
    def config_dir(self) -> Path:
        return self.home_dir / ".fesium"

    @property
    def legacy_config_dir(self) -> Path:
        return self.home_dir / ".nanoserver"
