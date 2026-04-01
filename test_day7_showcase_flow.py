from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from tests.test_day7_showcase_flow import main


if __name__ == "__main__":
    raise SystemExit(main())
