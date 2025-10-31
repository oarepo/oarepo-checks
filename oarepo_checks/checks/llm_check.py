"""LLM check implementation."""

import json
from typing import Dict, List

import requests
from invenio_checks.base import Check
from invenio_checks.contrib.metadata.check import CheckResult
from invenio_checks.models import CheckConfig

from oarepo_checks.config import CHAT_EINFRA_TOKEN, DEFAULT_PROMPT


class LLMCheck(Check):
    """Check for validating record using LLM."""

    id = "llm"
    title = "LLM validation"
    description = "Validates record using LLM."
    sort_order = 10

    def validate_config(self, config):
        """Validate the configuration for this metadata check."""
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        prompts = config.get("prompts")
        if not prompts or not isinstance(prompts, list):
            raise ValueError("Configuration must contain a 'prompts' list")

        for prompt in prompts:
            if not isinstance(prompt, str):
                raise ValueError("Each prompt must be a string")
        return True

    def run(self, record, config: CheckConfig):
        """Run the metadata check on a record with the given configuration."""
        # Create a check result
        result = CheckResult(self.id)
        # TODO: get prompt from config
        # prompt = config.params.get("prompts")[0]

        serialized_full_record = json.dumps(dict(record))
        prompt = DEFAULT_PROMPT.replace("{{record_serialized}}", serialized_full_record)

        # Stupid way for now, later we can make it configurable
        url = "https://chat.ai.e-infra.cz/api/chat/completions"
        token = CHAT_EINFRA_TOKEN
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        data = {
            "model": "deepseek-r1",
            "messages": [{"role": "user", "content": prompt}],
        }
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()
        llm_output = response_json["choices"][0]["message"]["content"]

        result = self.to_service_errors(llm_output)

        return result

    def to_service_errors(self, llm_output: str) -> List[Dict]:
        """Create error messages for the UI."""
        json_output = json.loads(llm_output)

        output = []

        for path, messages in json_output.items():
            output.append(
                {
                    "field": path,
                    "messages": [messages],
                    "description": "LLM generated errors",
                    "severity": "warning",
                }
            )

        return output
