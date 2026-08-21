"""Root launcher for Fesium.

This file shares its name with the real package in ``src/fesium/``. Running
``python fesium.py`` is fine - the file becomes ``__main__`` - but anything
that does ``import fesium`` from the repo root resolves the name to *this*
file instead of the package. Two lines keep both paths working:

* ``src`` goes on ``sys.path``, so ``fesium.*`` resolves to the real package.
* ``__path__`` makes this module behave like that package, so ``fesium.app``
  and its siblings keep importing.

Once the project is installed (``pip install -e .``), prefer ``python -m
fesium`` or the ``fesium`` console script. Neither needs this shim, and this
file can be dropped when the launcher no longer shares the package name.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

__path__ = [str(SRC / "fesium")]

# Resolved through __path__ above, so `import fesium` from the repo root still
# reports the real package version.
from fesium._version import __version__  # noqa: E402

__all__ = ["__version__", "main"]


def main() -> None:
    # Imported lazily: starting the UI pulls in customtkinter, which the
    # import paths above should not pay for.
    from fesium.app import main as run_app

    run_app()


if __name__ == "__main__":
    main()
