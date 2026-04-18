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
