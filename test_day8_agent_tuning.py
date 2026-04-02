from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from tests.test_day8_agent_tuning import main


if __name__ == "__main__":
    raise SystemExit(main())
