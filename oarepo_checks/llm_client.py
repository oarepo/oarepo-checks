#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""LLM Client for making requests to Language Model APIs."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any

import requests


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def chat_completion(self, prompt: str, **kwargs: Any) -> str:
        """Send a chat completion request to the LLM.

        :param prompt: The user prompt to send
        :param kwargs: Additional parameters specific to the implementation

        :returns: The LLM response as a string. String should be a parsable, correct JSON
        """


class ChatEInfraClient(BaseLLMClient):
    """Client for chat.ai.e-infra.cz API."""

    def __init__(
        self,
        api_token: str,
        api_url: str = "https://chat.ai.e-infra.cz/api/chat/completions",
        model: str = "deepseek-r1",
    ):
        """Initialize the ChatEInfra client.

        :param api_token: Bearer token for authentication
        :param api_url: API endpoint URL
        :param model: Model name to use for completions
        """
        self.api_token = api_token
        self.api_url = api_url
        self.model = model

    def chat_completion(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Send a chat completion request to the ChatEInfra API.

        :param prompt: The user prompt to send
        :param model: Override the default model
        :param temperature: Sampling temperature (0-2).
        Controls the randomness of the output. Low values = more deterministic, high values = more creative
        :param max_tokens: Maximum tokens in the response
        :param kwargs: Additional parameters to pass to the API

        :returns: The LLM response content as a string that is parsable JSON

        :raises: requests.RequestException: If the API request fails
        :raises: KeyError: If the response format is unexpected
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        data: dict[str, Any] = {
            "model": model or self.model,
            "messages": [{"role": "user", "content": prompt}],
        }

        # Add optional parameters if provided
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        # Merge any additional kwargs
        data.update(kwargs)

        response = requests.post(self.api_url, headers=headers, json=data)  # noqa: S113
        response.raise_for_status()  # Raise exception for bad status codes

        response_json = response.json()
        llm_output = response_json["choices"][0]["message"]["content"]
        # Clean up possible markdown formatting
        return re.sub(r"^```json|```$", "", llm_output.strip(), flags=re.MULTILINE).strip()
