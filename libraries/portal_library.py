"""Robot keywords for local mock lifecycle, configuration, and browser options."""

from __future__ import annotations

import json
import logging
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import TextIO

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from libraries.configuration import validate_configuration

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class PortalLibrary:
    """Start, inspect, and reset the test-only mock portal."""

    ROBOT_LIBRARY_SCOPE = "SUITE"

    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None
        self._temporary_directory: tempfile.TemporaryDirectory[str] | None = None
        self._log_file: TextIO | None = None
        self._portal_url = ""

    def validate_configuration(
        self,
        browser: str,
        portal_url: str,
        username: str,
        password: str,
        timeout: int,
        window_size: str,
        ci: bool,
    ) -> None:
        """Validate all runtime settings and reject invalid CI values."""
        validate_configuration(browser, portal_url, username, password, timeout, window_size)
        if not isinstance(ci, bool):
            raise ValueError("CI must be true or false.")

    def start_mock_portal(self) -> str:
        """Launch the loopback-only Flask server and return its selected URL."""
        if self._process is not None and self._process.poll() is None:
            raise RuntimeError("The mock portal is already running.")

        self._temporary_directory = tempfile.TemporaryDirectory(prefix="benefits-portal-")
        ready_file = Path(self._temporary_directory.name) / "ready.json"
        results_directory = PROJECT_ROOT / "results"
        results_directory.mkdir(parents=True, exist_ok=True)
        log_path = results_directory / "mock-portal.log"
        self._log_file = log_path.open("w", encoding="utf-8")
        command = [
            sys.executable,
            "-m",
            "mock_portal.server",
            "--port",
            "0",
            "--ready-file",
            str(ready_file),
        ]

        try:
            self._process = subprocess.Popen(
                command,
                cwd=PROJECT_ROOT,
                stdout=self._log_file,
                stderr=subprocess.STDOUT,
            )
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if ready_file.is_file():
                    ready_payload = json.loads(ready_file.read_text(encoding="utf-8"))
                    if not isinstance(ready_payload, dict):
                        raise RuntimeError("The mock portal returned a malformed ready signal.")
                    port = ready_payload.get("port")
                    if not isinstance(port, int) or not 1 <= port <= 65535:
                        raise RuntimeError("The mock portal returned an invalid ready signal.")
                    self._portal_url = f"http://127.0.0.1:{port}"
                    return self._portal_url
                if self._process.poll() is not None:
                    raise RuntimeError(
                        f"The mock portal exited during startup; see {log_path} for details."
                    )
                time.sleep(0.1)
            raise TimeoutError(
                f"The mock portal did not publish its ready signal; see {log_path} for details."
            )
        except (OSError, RuntimeError, json.JSONDecodeError):
            self.stop_mock_portal()
            raise

    def wait_for_portal_health(self, portal_url: str, timeout: int) -> None:
        """Wait for the portal health endpoint or fail with the last transport error."""
        health_url = f"{portal_url.rstrip('/')}/health"
        deadline = time.monotonic() + timeout
        last_error = "no response received"
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(health_url, timeout=1) as response:
                    if response.status == 200:
                        return
                    last_error = f"HTTP {response.status}"
            except OSError as error:
                last_error = str(error)
            time.sleep(0.1)
        raise TimeoutError(f"Portal health check failed for {health_url}: {last_error}")

    def reset_portal_state(self, portal_url: str) -> None:
        """Reset the local mock between tests; do not mutate external systems."""
        if self._process is None:
            LOGGER.info(
                "External portal mode selected; the external test environment was not reset."
            )
            return
        request = urllib.request.Request(
            f"{portal_url.rstrip('/')}/__reset",
            data=b"",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status != 200:
                    raise RuntimeError(f"Mock portal reset failed with HTTP {response.status}.")
        except OSError as error:
            raise RuntimeError("Mock portal reset request failed.") from error

    def stop_mock_portal(self) -> None:
        """Stop the child process and release its temporary ready-signal directory."""
        process = self._process
        self._process = None
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None
        if self._temporary_directory is not None:
            self._temporary_directory.cleanup()
            self._temporary_directory = None
        self._portal_url = ""

    def get_browser_options(
        self,
        browser: str,
        headless: bool,
        ci: bool,
    ) -> ChromeOptions | FirefoxOptions:
        """Create Selenium 4 browser options for the configured runtime."""
        normalized_browser = browser.strip().lower()
        if normalized_browser == "chrome":
            options = ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            if ci:
                options.add_argument("--no-sandbox")
            return options
        if normalized_browser == "firefox":
            firefox_options = FirefoxOptions()
            if headless:
                firefox_options.add_argument("-headless")
            return firefox_options
        raise ValueError("BROWSER must be either 'chrome' or 'firefox'.")

    @staticmethod
    def safe_screenshot_name(test_name: str) -> str:
        """Replace filesystem-sensitive characters in a test title."""
        return re.sub(r'[<>:"/\\|?*]', "_", test_name).strip()
