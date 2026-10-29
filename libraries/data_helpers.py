"""Pure data helpers used by the mock portal and test suite."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(slots=True)
class CoverageBalance:
    """Coverage limit and current remaining balance, both expressed in dollars."""

    limit: Decimal
    remaining: Decimal


def seeded_balances() -> dict[str, CoverageBalance]:
    """Return fresh seeded coverage balances for an independent test."""
    return {
        "health": CoverageBalance(limit=Decimal("2500.00"), remaining=Decimal("1200.00")),
        "dental": CoverageBalance(limit=Decimal("1500.00"), remaining=Decimal("800.00")),
    }


def parse_claim_amount(raw_amount: str) -> Decimal:
    """Parse a positive amount with at most two decimal places."""
    try:
        amount = Decimal(raw_amount.strip())
    except (InvalidOperation, ValueError) as error:
        raise ValueError("Enter a valid claim amount.") from error

    if not amount.is_finite():
        raise ValueError("Enter a valid claim amount.")
    decimal_places = amount.as_tuple().exponent
    if not isinstance(decimal_places, int) or decimal_places < -2:
        raise ValueError("Claim amount can have no more than two decimal places.")
    if amount <= 0:
        raise ValueError("Claim amount must be greater than zero.")
    return amount


def format_currency(amount: Decimal) -> str:
    """Format a monetary value for the mock portal UI."""
    return f"${amount:,.2f}"
