from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_DIR = ROOT / "python"

if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from tests.test_day2_pipeline import main


if __name__ == "__main__":
    raise SystemExit(main())
