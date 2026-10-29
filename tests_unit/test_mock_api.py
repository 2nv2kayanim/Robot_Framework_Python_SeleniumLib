"""Flask test-client coverage for the local-only benefits portal mock."""

from flask.testing import FlaskClient

from mock_portal.server import (
    INVALID_EMAIL,
    INVALID_PASSWORD,
    SEEDED_USERS,
    VALID_EMAIL,
    VALID_PASSWORD,
    create_app,
)


def authenticated_client() -> FlaskClient:
    client = create_app().test_client()
    response = client.post(
        "/login",
        data={"email": VALID_EMAIL, "password": VALID_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 302
    return client


def test_health_endpoint_announces_test_only_service() -> None:
    response = create_app().test_client().get("/health")
    assert response.status_code == 200
    assert response.json == {
        "purpose": "test-framework-development-only",
        "status": "ok",
    }


def test_invalid_seeded_credentials_are_rejected() -> None:
    assert len(SEEDED_USERS) == 2
    client = create_app().test_client()
    response = client.post(
        "/login",
        data={"email": INVALID_EMAIL, "password": INVALID_PASSWORD},
    )
    assert response.status_code == 401
    assert b"Email or password is incorrect." in response.data


def test_health_claim_reduces_balance() -> None:
    client = authenticated_client()
    response = client.post(
        "/claims",
        data={
            "claim_type": "health",
            "amount": "125.00",
            "claim_date": "2026-10-28",
            "description": "Routine health visit",
        },
    )
    assert response.status_code == 200
    assert b"Health claim submitted successfully." in response.data
    assert b"$1,075.00" in client.get("/benefits").data


def test_claim_equal_to_remaining_balance_is_accepted() -> None:
    client = authenticated_client()
    response = client.post(
        "/claims",
        data={
            "claim_type": "health",
            "amount": "1200.00",
            "claim_date": "2026-10-28",
            "description": "Full remaining balance",
        },
    )
    assert response.status_code == 200
    assert b"$0.00" in client.get("/benefits").data


def test_one_cent_over_remaining_balance_is_rejected_without_deduction() -> None:
    client = authenticated_client()
    response = client.post(
        "/claims",
        data={
            "claim_type": "health",
            "amount": "1200.01",
            "claim_date": "2026-10-28",
            "description": "One cent too much",
        },
    )
    assert response.status_code == 400
    assert b"exceeds remaining health coverage balance" in response.data
    assert b"$1,200.00" in client.get("/benefits").data


def test_zero_and_negative_claim_amounts_are_rejected() -> None:
    client = authenticated_client()
    for amount in ("0", "-1"):
        response = client.post(
            "/claims",
            data={
                "claim_type": "dental",
                "amount": amount,
                "claim_date": "2026-10-28",
                "description": "Invalid amount",
            },
        )
        assert response.status_code == 400
        assert b"Claim amount must be greater than zero." in response.data


def test_missing_fields_and_invalid_service_date_are_rejected() -> None:
    client = authenticated_client()
    missing_response = client.post("/claims", data={"claim_type": "health"})
    assert missing_response.status_code == 400
    assert b"Please complete all required fields." in missing_response.data

    invalid_date_response = client.post(
        "/claims",
        data={
            "claim_type": "health",
            "amount": "25.00",
            "claim_date": "not-a-date",
            "description": "Invalid date",
        },
    )
    assert invalid_date_response.status_code == 400
    assert b"valid service date" in invalid_date_response.data.lower()


def test_reset_restores_balances_and_clears_session() -> None:
    client = authenticated_client()
    client.post(
        "/claims",
        data={
            "claim_type": "dental",
            "amount": "20.00",
            "claim_date": "2026-10-28",
            "description": "Temporary claim",
        },
    )
    response = client.post("/__reset")
    assert response.status_code == 200
    assert response.json == {"status": "reset"}
    assert client.get("/benefits").status_code == 302

    fresh_client = authenticated_client()
    assert b"$800.00" in fresh_client.get("/benefits").data
