from http import HTTPStatus

import pytest

from mqp_dashboard_backend import request_access


@pytest.fixture(autouse=True)
def mail_environment(monkeypatch):
    """Provide deterministic mail settings without requiring private SMTP config."""

    monkeypatch.setenv("MQP_MAIL_DEFAULT_SENDER", "dashboard@example.test")
    monkeypatch.setenv("MQP_MAIL_ADMIN", "admin@example.test,backup@example.test")


@pytest.fixture
def sent_request_access_messages(monkeypatch):
    sent_messages = []
    monkeypatch.setattr(request_access.mail, "send", sent_messages.append)
    return sent_messages


def test_request_access_sends_admin_email(client, sent_request_access_messages) -> None:
    """Request access submissions are summarized in an admin email."""

    payload = {
        "title": "Dr.",
        "name": "Ada Lovelace",
        "email": "ada@example.test",
        "userID": "ada123",
        "project": "Quantum Algorithms",
        "country": "Germany",
        "organization": "MQP Institute",
        "message": "Please grant access.",
    }

    response = client.post("/request_access", json=payload)

    message = sent_request_access_messages[0]

    assert response.status_code == HTTPStatus.OK
    assert response.json == {"message": "Mail has sent"}
    assert len(sent_request_access_messages) == 1
    assert message.subject == "New Request Access"
    assert message.sender == "MQP-Dashboard <dashboard@example.test>"
    assert message.recipients == ["admin@example.test,backup@example.test"]
    assert "Name: </th><td>Dr.&nbsp;Ada Lovelace" in message.html
    assert "Email Address: </th><td>ada@example.test" in message.html
    assert "User-ID: </th><td>ada123" in message.html
    assert "Project Name: </th><td>Quantum Algorithms" in message.html
    assert "Country: </th><td>Germany" in message.html
    assert "Organization/Institute: </th><td>MQP Institute" in message.html
    assert "Message: </th><td>Please grant access." in message.html


def test_request_access_missing_required_field_fails_before_sending_email(
    client, sent_request_access_messages
) -> None:
    """Existing request-access behavior raises for incomplete payloads."""

    with pytest.raises(KeyError, match="organization"):
        client.post(
            "/request_access",
            json={
                "title": "Dr.",
                "name": "Ada Lovelace",
                "email": "ada@example.test",
                "userID": "ada123",
                "project": "Quantum Algorithms",
                "country": "Germany",
                "message": "Please grant access.",
            },
        )

    assert sent_request_access_messages == []
