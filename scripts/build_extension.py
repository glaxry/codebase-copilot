from __future__ import annotations

import json
import locale
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = ROOT / "build" / "day1"
CPP_DIR = ROOT / "cpp"
VENDOR_DIR = ROOT / ".vendor"


def _run(command: list[str]) -> None:
    print(">", " ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def _find_cmake() -> str:
    direct = shutil.which("cmake")
    if direct:
        return direct

    vswhere = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe")
    if not vswhere.exists():
        raise FileNotFoundError("Cannot locate cmake and vswhere is unavailable.")

    output = subprocess.check_output(
        [str(vswhere), "-latest", "-products", "*", "-format", "json"],
        text=True,
        encoding=locale.getpreferredencoding(False),
        errors="replace",
    )
    installations = json.loads(output)
    if not installations:
        raise FileNotFoundError("No Visual Studio installation found for CMake discovery.")

    install_path = Path(installations[0]["installationPath"])
    cmake_path = install_path / "Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe"
    if not cmake_path.exists():
        raise FileNotFoundError(f"CMake not found under Visual Studio: {cmake_path}")
    return str(cmake_path)


def _find_pybind11_cmake_dir() -> str:
    try:
        import pybind11  # type: ignore
    except ImportError:
        if VENDOR_DIR.exists():
            sys.path.insert(0, str(VENDOR_DIR))
            import pybind11  # type: ignore
        else:
            raise ModuleNotFoundError(
                "pybind11 is not installed in the active Python environment. "
                "Activate your environment and run `python -m pip install -r requirements.txt`."
            )

    return pybind11.get_cmake_dir()


def main() -> int:
    cmake = _find_cmake()
    pybind11_dir = _find_pybind11_cmake_dir()
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    configure_command = [
        cmake,
        "-S",
        str(CPP_DIR),
        "-B",
        str(BUILD_DIR),
        "-G",
        "Visual Studio 17 2022",
        "-A",
        "x64",
        f"-Dpybind11_DIR={pybind11_dir}",
        f"-DPython_EXECUTABLE={sys.executable}",
        "-DPYBIND11_FINDPYTHON=ON",
    ]
    build_command = [
        cmake,
        "--build",
        str(BUILD_DIR),
        "--config",
        "Release",
    ]

    _run(configure_command)
    _run(build_command)
    print("Native extension build completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
