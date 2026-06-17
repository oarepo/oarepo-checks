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
from typing import TYPE_CHECKING, cast

from invenio_access.permissions import system_identity
from invenio_checks.base import Check
from invenio_checks.contrib.metadata.check import CheckResult
from invenio_i18n import get_locale
from oarepo_runtime.proxies import current_runtime

if TYPE_CHECKING:
    from invenio_checks.models import CheckConfig
    from invenio_drafts_resources.services import RecordService
    from invenio_records.api import Record


class LLMCheck(Check):
    """Check for validating record using LLM."""

    id = "llm"
    title = "AI validation"
    description = "Validates record using AI."

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
        result = CheckResult(self.id, sync=False)

        # Serialize the record
        try:
            model = current_runtime.get_model_for_record(record)
            svc = cast("RecordService", model.service)
            serialized_full_record = svc.read_draft(system_identity, record["id"], expand=True).to_dict()
        except:  # noqa: E722
            # fallback to serializing the record manually (might not contain some fields)
            json_record = dict(record)
            serialized_full_record = json.dumps(json_record)

        # Get the pre-rendered prompt from config and replace the record placeholder
        prompt = config.params.get("prompt", "")
        prompt = prompt.replace("{{record_serialized}}", json.dumps(serialized_full_record))
        prompt = prompt.replace("{{language}}", str(get_locale()))

        # TODO: check for prompt length (depending on the LLM used) so we are not out of context window

        from oarepo_checks.tasks import run_llm_check

        run_llm_check.delay(
            prompt=prompt,
            record_id=str(record.id),
            config_id=str(config.id),
        )

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
