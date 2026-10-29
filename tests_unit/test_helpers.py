"""Tests for configuration and monetary-value helpers."""

from decimal import Decimal

import pytest

from libraries.configuration import validate_configuration
from libraries.data_helpers import format_currency, parse_claim_amount, seeded_balances


@pytest.mark.parametrize("raw_amount", ["0", "-1", "-0.01"])
def test_amount_must_be_positive(raw_amount: str) -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        parse_claim_amount(raw_amount)


@pytest.mark.parametrize("raw_amount", ["", "not-a-number", "NaN", "Infinity", "1.001"])
def test_amount_must_be_a_finite_value_with_two_decimals(raw_amount: str) -> None:
    with pytest.raises(ValueError):
        parse_claim_amount(raw_amount)


def test_claim_amount_accepts_integer_and_cents() -> None:
    assert parse_claim_amount("125") == Decimal("125")
    assert parse_claim_amount("1200.01") == Decimal("1200.01")


def test_currency_format_uses_two_decimal_places() -> None:
    assert format_currency(Decimal("1200")) == "$1,200.00"


def test_seeded_balances_are_fresh_for_each_test() -> None:
    first = seeded_balances()
    first["health"].remaining = Decimal("0.00")
    second = seeded_balances()
    assert second["health"].remaining == Decimal("1200.00")
    assert second["health"].limit == Decimal("2500.00")
    assert second["dental"].remaining == Decimal("800.00")


def test_configuration_accepts_local_defaults() -> None:
    validate_configuration("chrome", "", "member@example.test", "mock-password", 10, "1440x1000")


@pytest.mark.parametrize(
    ("browser", "portal_url", "username", "password", "timeout", "window_size", "message"),
    [
        ("safari", "", "member", "password", 10, "1440x1000", "BROWSER"),
        ("chrome", "https://portal.example.test", "", "", 10, "1440x1000", "External portal"),
        ("chrome", "", "member", "password", 0, "1440x1000", "TIMEOUT"),
        ("chrome", "", "member", "password", 10, "0x1000", "WINDOW_SIZE"),
        ("chrome", "not-a-url", "member", "password", 10, "1440x1000", "PORTAL_URL"),
    ],
)
def test_invalid_configuration_fails_loudly(
    browser: str,
    portal_url: str,
    username: str,
    password: str,
    timeout: int,
    window_size: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_configuration(browser, portal_url, username, password, timeout, window_size)
