from __future__ import annotations

import requests

from oarepo_checks.llm_client import ChatEInfraClient


REQUEST_CALLS = []
REQUEST_DATA = {}


class Response:
    def __init__(self, content):
        self.content = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


def post(url, headers, json, timeout):
    REQUEST_CALLS.append(
        {
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": timeout,
        }
    )
    return Response('{"ok": true}')


def post_default_model(url, headers, json, timeout):
    REQUEST_DATA.update(json)
    return Response("{}")


def test_llm_client(monkeypatch):
    REQUEST_CALLS.clear()
    REQUEST_DATA.clear()
    monkeypatch.setattr(requests, "post", post)

    client = ChatEInfraClient(
        api_token="token",
        api_url="https://example.test/chat",
        model="default-model",
    )

    result = client.chat_completion(
        "prompt",
        model="custom-model",
        temperature=0.1,
        max_tokens=100,
        top_p=0.9,
    )

    assert result == '{"ok": true}'
    assert REQUEST_CALLS == [
        {
            "url": "https://example.test/chat",
            "headers": {
                "Authorization": "Bearer token",
                "Content-Type": "application/json",
            },
            "json": {
                "model": "custom-model",
                "messages": [{"role": "user", "content": "prompt"}],
                "temperature": 0.1,
                "max_tokens": 100,
                "top_p": 0.9,
            },
            "timeout": 60,
        }
    ]

    monkeypatch.setattr(requests, "post", post_default_model)

    client = ChatEInfraClient(api_token="token", model="default-model")

    assert client.chat_completion("prompt") == "{}"
    assert REQUEST_DATA["model"] == "default-model"

