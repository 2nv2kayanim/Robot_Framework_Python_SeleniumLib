"""TEST-FRAMEWORK DEVELOPMENT ONLY. Never expose or use this mock in production."""

from __future__ import annotations

import argparse
import json
import secrets
from datetime import date
from pathlib import Path
from threading import RLock
from typing import TypedDict
from uuid import uuid4

from flask import (
    Flask,
    jsonify,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from werkzeug.serving import BaseWSGIServer, make_server
from werkzeug.wrappers import Response

from libraries.data_helpers import (
    CoverageBalance,
    format_currency,
    parse_claim_amount,
    seeded_balances,
)

VALID_EMAIL = "member@example.test"
VALID_PASSWORD = "MockBenefits!2026"
INVALID_EMAIL = "locked-member@example.test"
INVALID_PASSWORD = "DisabledMember!2026"


class SeededUser(TypedDict):
    password: str
    enabled: bool


SEEDED_USERS: dict[str, SeededUser] = {
    VALID_EMAIL: {"password": VALID_PASSWORD, "enabled": True},
    INVALID_EMAIL: {"password": INVALID_PASSWORD, "enabled": False},
}

LOGIN_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Group Benefits Portal - Sign in</title></head>
<body><main><h1>Group Benefits Portal</h1><p>TEST MOCK - not a real benefits service.</p>
<form method="post" action="{{ url_for('login') }}">
<label for="email">Email</label>
<input id="email" name="email" type="email" data-testid="login-email" required>
<label for="password">Password</label>
<input id="password" name="password" type="password" data-testid="login-password" required>
<button type="submit" data-testid="login-submit">Sign in</button>
{% if error %}<p role="alert" data-testid="login-error">{{ error }}</p>{% endif %}
</form></main></body></html>"""

DASHBOARD_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Benefits dashboard</title></head>
<body><main><h1>Benefits dashboard</h1><p>TEST MOCK - seeded coverage only.</p>
<section aria-label="Health coverage"><h2>Health</h2>
<p>Coverage limit: <strong data-testid="health-limit">{{ health_limit }}</strong></p>
<p>Remaining: <strong data-testid="health-remaining">{{ health_remaining }}</strong></p></section>
<section aria-label="Dental coverage"><h2>Dental</h2>
<p>Coverage limit: <strong data-testid="dental-limit">{{ dental_limit }}</strong></p>
<p>Remaining: <strong data-testid="dental-remaining">{{ dental_remaining }}</strong></p></section>
<a href="{{ url_for('new_claim') }}" data-testid="claim-navigation">Submit a claim</a>
<a href="{{ url_for('logout') }}" data-testid="logout">Sign out</a>
</main></body></html>"""

CLAIM_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Submit a claim</title></head>
<body><main><h1>Submit a claim</h1><p>TEST MOCK - no real claims are created.</p>
<form method="post" action="{{ url_for('submit_claim') }}">
<label for="claim-type">Coverage type</label>
<select id="claim-type" name="claim_type" data-testid="claim-type" required>
<option value="" data-testid="claim-empty-option">Choose coverage</option>
<option value="health" data-testid="claim-health-option"
{% if claim_type == 'health' %}selected{% endif %}>Health</option>
<option value="dental" data-testid="claim-dental-option"
{% if claim_type == 'dental' %}selected{% endif %}>Dental</option>
</select>
<label for="amount">Amount</label>
<input id="amount" name="amount" type="number" step="0.01" data-testid="claim-amount"
value="{{ amount }}" required>
<label for="claim-date">Service date</label>
<input id="claim-date" name="claim_date" type="date" data-testid="claim-date"
value="{{ claim_date }}" required>
<label for="description">Description</label>
<textarea id="description" name="description" data-testid="claim-description"
required>{{ description }}</textarea>
<button type="submit" data-testid="claim-submit">Submit claim</button>
{% if error %}<p role="alert" data-testid="claim-error">{{ error }}</p>{% endif %}
</form></main></body></html>"""

CONFIRMATION_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Claim confirmation</title></head>
<body><main><h1>Claim submitted</h1>
<p data-testid="claim-confirmation">{{ message }}</p>
<p>Claim reference: <strong data-testid="claim-reference">{{ claim_reference }}</strong></p>
<a href="{{ url_for('benefits') }}" data-testid="dashboard-navigation">Return to benefits</a>
</main></body></html>"""


class PortalState:
    """Mutable mock data isolated to one local server process."""

    def __init__(self) -> None:
        self.balances: dict[str, CoverageBalance] = seeded_balances()
        self.lock = RLock()

    def reset(self) -> None:
        with self.lock:
            self.balances = seeded_balances()


def create_app() -> Flask:
    """Create an isolated test-only Flask application."""
    application = Flask(__name__)
    application.secret_key = secrets.token_hex(32)
    portal_state = PortalState()
    application.extensions["portal_state"] = portal_state

    def state() -> PortalState:
        return portal_state

    def signed_in() -> bool:
        return session.get("authenticated") is True

    def claim_form(
        error: str = "",
        claim_type: str = "",
        amount: str = "",
        claim_date: str = "",
        description: str = "",
        status: int = 200,
    ) -> tuple[str, int]:
        return (
            render_template_string(
                CLAIM_PAGE,
                error=error,
                claim_type=claim_type,
                amount=amount,
                claim_date=claim_date,
                description=description,
            ),
            status,
        )

    @application.get("/")
    def index() -> Response:
        return redirect(url_for("login"))

    @application.get("/health")
    def health() -> Response:
        return jsonify({"status": "ok", "purpose": "test-framework-development-only"})

    @application.get("/login")
    def login_page() -> str:
        return render_template_string(LOGIN_PAGE, error="")

    @application.post("/login")
    def login() -> tuple[str, int] | Response:
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        member = SEEDED_USERS.get(email)
        if (
            member is not None
            and member["enabled"]
            and secrets.compare_digest(password, member["password"])
        ):
            session["authenticated"] = True
            return redirect(url_for("benefits"))
        return render_template_string(LOGIN_PAGE, error="Email or password is incorrect."), 401

    @application.get("/logout")
    def logout() -> Response:
        session.clear()
        return redirect(url_for("login"))

    @application.get("/benefits")
    def benefits() -> str | Response:
        if not signed_in():
            return redirect(url_for("login"))
        with state().lock:
            balances = state().balances.copy()
            health = balances["health"]
            dental = balances["dental"]
            return render_template_string(
                DASHBOARD_PAGE,
                health_limit=format_currency(health.limit),
                health_remaining=format_currency(health.remaining),
                dental_limit=format_currency(dental.limit),
                dental_remaining=format_currency(dental.remaining),
            )

    @application.get("/claims/new")
    def new_claim() -> str | Response | tuple[str, int]:
        if not signed_in():
            return redirect(url_for("login"))
        return claim_form()

    @application.post("/claims")
    def submit_claim() -> str | tuple[str, int] | Response:
        if not signed_in():
            return redirect(url_for("login"))

        claim_type = request.form.get("claim_type", "").strip().lower()
        amount_text = request.form.get("amount", "").strip()
        claim_date = request.form.get("claim_date", "").strip()
        description = request.form.get("description", "").strip()
        if not claim_type or not amount_text or not claim_date or not description:
            return claim_form(
                "Please complete all required fields.",
                claim_type,
                amount_text,
                claim_date,
                description,
                400,
            )
        if claim_type not in {"health", "dental"}:
            return claim_form(
                "Choose health or dental coverage.",
                claim_type,
                amount_text,
                claim_date,
                description,
                400,
            )
        try:
            amount = parse_claim_amount(amount_text)
        except ValueError as error:
            return claim_form(
                str(error),
                claim_type,
                amount_text,
                claim_date,
                description,
                400,
            )
        try:
            date.fromisoformat(claim_date)
        except ValueError:
            return claim_form(
                "Enter a valid service date.",
                claim_type,
                amount_text,
                claim_date,
                description,
                400,
            )

        with state().lock:
            coverage = state().balances[claim_type]
            if amount > coverage.remaining:
                message = (
                    f"Claim amount exceeds remaining {claim_type} coverage balance "
                    f"of {format_currency(coverage.remaining)}."
                )
                return claim_form(
                    message,
                    claim_type,
                    amount_text,
                    claim_date,
                    description,
                    400,
                )
            coverage.remaining -= amount

        return render_template_string(
            CONFIRMATION_PAGE,
            message=f"{claim_type.title()} claim submitted successfully.",
            claim_reference=uuid4().hex[:12].upper(),
        )

    @application.post("/__reset")
    def reset() -> Response:
        state().reset()
        session.clear()
        return jsonify({"status": "reset"})

    return application


app = create_app()


def _write_ready_signal(path: Path, port: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(json.dumps({"port": port}), encoding="utf-8")
    temporary_path.replace(path)


def serve(port: int, ready_file: Path | None) -> None:
    """Bind the development server exclusively to loopback and publish readiness."""
    server: BaseWSGIServer = make_server("127.0.0.1", port, app, threaded=True)
    if ready_file is not None:
        _write_ready_signal(ready_file, int(server.server_port))
    server.serve_forever()


def main() -> None:
    """Start the test mock on a fixed or automatically selected local port."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--ready-file", type=Path)
    arguments = parser.parse_args()
    if not 0 <= arguments.port <= 65535:
        parser.error("--port must be between 0 and 65535.")
    serve(arguments.port, arguments.ready_file)


if __name__ == "__main__":
    main()
