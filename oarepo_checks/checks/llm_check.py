#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""LLM check implementation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from invenio_checks.base import Check
from invenio_checks.contrib.metadata.check import CheckResult

from oarepo_checks.proxies import current_oarepo_checks

if TYPE_CHECKING:
    from invenio_checks.models import CheckConfig
    from invenio_records.api import Record


class LLMCheck(Check):
    """Check for validating record using LLM."""

    id = "llm"
    title = "LLM validation"
    description = "Validates record using LLM."

    def validate_config(self, config: CheckConfig) -> bool:
        """Validate the configuration for this metadata check."""
        if not isinstance(config, dict):
            raise TypeError("Configuration must be a dictionary")

        # Check for prompt string
        prompt = config.get("prompt")
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Configuration must contain a 'prompt' string")

        return True

    def run(self, record: Record, config: CheckConfig) -> CheckResult:
        """Run the metadata check on a record with the given configuration."""
        # Create a check result
        result = CheckResult(self.id)

        # Serialize the record
        serialized_full_record = json.dumps(dict(record))

        # Get the pre-rendered prompt from config and replace the record placeholder
        prompt = config.params.get("prompt", "")
        prompt = prompt.replace("{{record_serialized}}", serialized_full_record)

        # TODO: check for prompt length (depending on the LLM used) so we are not out of context window

        # Use the LLM client to get the response
        if current_oarepo_checks.llm_client is None:
            raise RuntimeError("No LLM client configured for oarepo-checks")

        json_with_errors = current_oarepo_checks.llm_client.chat_completion(prompt)

        errors = self.parse_errors(json_with_errors)
        result.errors.extend(errors)

        return result

    def parse_errors(self, llm_output: str) -> list[dict]:
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
