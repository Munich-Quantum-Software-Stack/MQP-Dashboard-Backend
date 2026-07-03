from http import HTTPStatus

import pytest

from mqp_dashboard_backend import feedbacks


@pytest.fixture(autouse=True)
def mail_environment(monkeypatch):
    """Provide deterministic mail settings without requiring private SMTP config."""

    monkeypatch.setenv("MQP_MAIL_DEFAULT_SENDER", "dashboard@example.test")
    monkeypatch.setenv("MQP_MAIL_ADMIN", "admin@example.test,backup@example.test")


@pytest.fixture
def sent_feedback_messages(monkeypatch):
    sent_messages = []
    monkeypatch.setattr(feedbacks.mail, "send", sent_messages.append)
    return sent_messages


def test_new_feedback_saves_feedback_and_sends_admin_email(
    active_client, monkeypatch, sent_feedback_messages
) -> None:
    """Feedback submissions are persisted and summarized in an admin email."""

    created_feedbacks = []

    def fake_create_feedback_for_identity(identity, rate, category, note):
        created_feedbacks.append(
            {
                "identity": identity,
                "rate": rate,
                "category": category,
                "note": note,
            }
        )

    monkeypatch.setattr(
        feedbacks.database.feedback,
        "create_feedback_for_identity",
        fake_create_feedback_for_identity,
    )

    payload = {"rate": 5, "category": "UX", "note": "The dashboard is helpful."}
    response = active_client.post(
        "/feedbacks/new", json=payload, headers=active_client.headers
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json == {"message": "Mail has sent"}
    assert created_feedbacks == [
        {
            "identity": "test_user",
            "rate": 5,
            "category": "UX",
            "note": "The dashboard is helpful.",
        }
    ]

    message = sent_feedback_messages[0]

    assert len(sent_feedback_messages) == 1
    assert message.subject == "New feedback"
    assert message.sender == "MQP-Dashboard <dashboard@example.test>"
    assert message.recipients == ["admin@example.test", "backup@example.test"]
    assert "Rating: </th><td>5" in message.html
    assert "Category: </th><td>UX" in message.html
    assert "Comment: </th><td>The dashboard is helpful." in message.html


def test_new_feedback_requires_jwt(client, sent_feedback_messages) -> None:
    """Feedback cannot be submitted without an access token."""

    response = client.post(
        "/feedbacks/new", json={"rate": 3, "category": "UX", "note": "No token"}
    )

    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert sent_feedback_messages == []


def test_new_feedback_missing_required_field_fails_before_sending_email(
    active_client, monkeypatch, sent_feedback_messages
) -> None:
    """Existing validation behavior raises for incomplete feedback payloads."""

    created_feedbacks = []
    monkeypatch.setattr(
        feedbacks.database.feedback,
        "create_feedback_for_identity",
        lambda *args: created_feedbacks.append(args),
    )

    with pytest.raises(KeyError, match="note"):
        active_client.post(
            "/feedbacks/new",
            json={"rate": 2, "category": "Bug"},
            headers=active_client.headers,
        )

    assert created_feedbacks == []
    assert sent_feedback_messages == []
