import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_root_launcher_imports_new_package():
    result = subprocess.run(
        [sys.executable, "-c", "import fesium; from fesium.app import main"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_module_entrypoint_resolves_without_the_root_shim():
    result = subprocess.run(
        [sys.executable, "-c", "import fesium.__main__ as entry; assert callable(entry.main)"],
        cwd=ROOT / "src",
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_root_launcher_does_not_execute_source_text():
    """The shim used to exec() the package __init__ to borrow __version__.

    fesium._version exists so a plain import does the same job. Keep it that
    way: exec() in a launcher is a code-execution surface for no benefit.
    """
    launcher = (ROOT / "fesium.py").read_text(encoding="utf-8")

    assert "exec(" not in launcher
    assert "eval(" not in launcher
