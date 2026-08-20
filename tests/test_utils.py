
from __future__ import annotations

from oarepo_checks.utils import check_error_messages, create_prompt


def test_check_error_message():
    #pridano
    messages = [
        "plain error",
        {"message": "message text"},
        {"error": "error text"},
        {"error_long": "long error text"},
        {"error_short": "short error text"},
        {"jej": "jej"},
        123,
    ]

    assert check_error_messages(messages) == [
        "plain error",
        "message text",
        "error text",
        "long error text",
        "short error text",
        "{'jej': 'jej'}",
        "123",
    ]



def test_check_prompt(app):
    #pridano
    community = {
        "metadata": {
            "title": "Test Community",
            "curation_policy": "Use a clear title.",
            "description": "Community description.",
        }
    }
    record_serialized = '{"metadata": {"title": "Test record"}}'

    prompt = create_prompt(
        record_serialized=record_serialized,
        community=community,
        language="cs",
    )

    assert record_serialized in prompt
    assert "Test Community" in prompt
    assert "Use a clear title." in prompt
    assert "Community description." in prompt
    assert "cs" in prompt
