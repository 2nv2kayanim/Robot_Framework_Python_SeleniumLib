"""Validation for browser and portal settings shared by Robot and unit tests."""

import re
from urllib.parse import urlparse

_WINDOW_SIZE_PATTERN = re.compile(r"^([1-9]\d*)x([1-9]\d*)$")


def validate_configuration(
    browser: str,
    portal_url: str,
    username: str,
    password: str,
    timeout: int,
    window_size: str,
) -> None:
    """Reject unsupported or incomplete runtime settings before starting a test."""
    normalized_browser = browser.strip().lower()
    if normalized_browser not in {"chrome", "firefox"}:
        raise ValueError("BROWSER must be either 'chrome' or 'firefox'.")
    if timeout <= 0:
        raise ValueError("TIMEOUT must be a positive number of seconds.")
    if _WINDOW_SIZE_PATTERN.fullmatch(window_size.strip()) is None:
        raise ValueError("WINDOW_SIZE must use the WIDTHxHEIGHT format, for example 1440x1000.")

    if portal_url.strip():
        parsed_url = urlparse(portal_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError("PORTAL_URL must be an absolute HTTP or HTTPS URL.")
        if not username.strip() or not password:
            raise ValueError("External portal mode requires PORTAL_USERNAME and PORTAL_PASSWORD.")
