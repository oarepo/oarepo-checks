"""LLM Client for making requests to Language Model APIs."""

import re
from abc import ABC, abstractmethod
from typing import Optional

import requests


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def chat_completion(self, prompt: str, **kwargs) -> str:
        """
        Send a chat completion request to the LLM.


        :param prompt: The user prompt to send
        :param **kwargs: Additional parameters specific to the implementation

        :returns: The LLM response as a string
        """
        pass


class ChatEInfraClient(BaseLLMClient):
    """Client for chat.ai.e-infra.cz API."""

    def __init__(
        self,
        api_token: str,
        api_url: str = "https://chat.ai.e-infra.cz/api/chat/completions",
        model: str = "deepseek-r1",
    ):
        """
        Initialize the ChatEInfra client.

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
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Send a chat completion request to the ChatEInfra API.


        :param prompt: The user prompt to send
        :param model: Override the default model
        :param temperature: Sampling temperature (0-2)
        :param max_tokens: Maximum tokens in the response
        :param kwargs: Additional parameters to pass to the API


        :returns: The LLM response content as a string

        :raises: requests.RequestException: If the API request fails, KeyError: If the response format is unexpected
        """
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        data = {
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

        response = requests.post(self.api_url, headers=headers, json=data)
        response.raise_for_status()  # Raise exception for bad status codes

        response_json = response.json()
        llm_output = response_json["choices"][0]["message"]["content"]
        # Clean up possible markdown formatting
        llm_output = re.sub(
            r"^```json|```$", "", llm_output.strip(), flags=re.MULTILINE
        ).strip()
        return llm_output
