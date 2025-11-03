"""LLM check implementation."""

import json
from typing import Dict, List

from invenio_checks.base import Check
from invenio_checks.contrib.metadata.check import CheckResult
from invenio_checks.models import CheckConfig

from oarepo_checks.proxies import current_oarepo_checks


class LLMCheck(Check):
    """Check for validating record using LLM."""

    id = "llm"
    title = "LLM validation"
    description = "Validates record using LLM."

    def validate_config(self, config):
        """Validate the configuration for this metadata check."""
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a dictionary")

        prompt = config.get("prompt")
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Configuration must contain a 'prompt' string")

        return True

    def run(self, record, config: CheckConfig):
        """Run the metadata check on a record with the given configuration."""
        # Create a check result
        result = CheckResult(self.id)
        prompt = config.params.get("prompt")

        serialized_full_record = json.dumps(dict(record))
        prompt = prompt.replace("{{record_serialized}}", serialized_full_record)

        # Use the LLM client to get the response
        json_with_errors = current_oarepo_checks.llm_client.chat_completion(prompt)

        errors = self.parse_errors(json_with_errors)
        result.errors.extend(errors)

        return result

    def parse_errors(self, llm_output: str) -> List[Dict]:
        """Create error messages for the UI."""
        json_output = json.loads(llm_output)

        output = []

        for path, info in json_output.items():
            if info.get("section_empty"):
                continue

            output.append(
                {
                    "field": path,
                    "messages": info["errors"],
                    "description": "LLM generated errors. Proceed with caution.",
                    "severity": "warning",
                }
            )

        return output
