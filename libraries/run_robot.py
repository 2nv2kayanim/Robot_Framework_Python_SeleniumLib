"""Run Robot Framework with Allure JSON results in the project results folder."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from robot import run_cli


def main() -> int:
    """Set up report paths and pass all arguments to Robot Framework."""
    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
    results_directory = project_root / "results"
    if results_directory.is_symlink():
        raise RuntimeError("The results directory must not be a symbolic link.")
    results_directory.mkdir(parents=True, exist_ok=True)
    allure_results = results_directory / "allure-results"
    if allure_results.is_symlink():
        raise RuntimeError("The Allure results directory must not be a symbolic link.")
    allure_results.mkdir(parents=True, exist_ok=True)
    for result_file in allure_results.iterdir():
        if result_file.is_dir() and not result_file.is_symlink():
            raise RuntimeError("Unexpected subdirectory found in the Allure results folder.")
        result_file.unlink()
    robot_arguments = [
        "--listener",
        "allure_robotframework:results/allure-results",
        *sys.argv[1:],
    ]
    return int(run_cli(robot_arguments, exit=False))


if __name__ == "__main__":
    raise SystemExit(main())
