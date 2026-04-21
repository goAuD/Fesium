"""Root launcher and package shim for Fesium.

This file sits next to a package that shares its name (``src/fesium/``). Run
it as ``python fesium.py`` and it becomes ``__main__``. But when a tool
``import fesium`` from the repo root, Python resolves the name to this file,
not to the package. The shim below makes both paths work:

* ``src`` is prepended to ``sys.path`` so ``fesium.*`` resolves to the real
  package.
* ``__path__`` makes this module act like a package pointing at the real
  package directory, keeping subpackage imports (``fesium.app``, etc.) alive.
* The package's ``__init__`` is executed into the launcher's globals so
  attributes like ``fesium.__version__`` are available on either import path.

Remove this shim once the project is installable (``pip install -e .``) and
the launcher no longer shares a name with the package.
"""

import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
PACKAGE_DIR = SRC / "fesium"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

__path__ = [str(PACKAGE_DIR)]
exec((PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8"), globals())


def main() -> None:
    importlib.import_module("fesium.app").main()


if __name__ == "__main__":
    main()
