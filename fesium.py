import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
PACKAGE_DIR = SRC / "fesium"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Make the root launcher behave like a package shim so `fesium.app`
# remains importable even though this file shares the package name.
__path__ = [str(PACKAGE_DIR)]

# Mirror the package metadata needed by submodules that import from `fesium`.
exec((PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8"), globals())


def main():
    app_module = importlib.import_module("fesium.app")
    return app_module.main()


if __name__ == "__main__":
    main()
