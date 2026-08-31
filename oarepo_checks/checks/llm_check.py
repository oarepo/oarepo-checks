# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""LLM check implementation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from flask import current_app
from invenio_access.permissions import system_identity
from invenio_checks.base import Check
from invenio_checks.contrib.metadata.check import CheckResult
from invenio_i18n import get_locale
from invenio_i18n import lazy_gettext as _
from oarepo_runtime.proxies import current_runtime

from oarepo_checks.proxies import current_oarepo_checks

if TYPE_CHECKING:
    from invenio_checks.models import CheckConfig
    from invenio_drafts_resources.services import RecordService
    from invenio_records.api import Record


class LLMCheck(Check):
    """Check for validating record using LLM."""

    id = "llm"
    title = _("AI validation")
    description = _("Validates record using AI.")

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
        if current_oarepo_checks.llm_client is None:
            result.sync = True
            return result

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

        max_prompt_chars = current_app.config.get("OAREPO_CHECKS_MAX_LLM_INPUT_CHARS", 2000000)
        if len(prompt) > max_prompt_chars:
            result.sync = True
            result.errors.append(
                {
                    "field": "files",
                    "messages": ["The record is too large for AI validation."],
                    "description": "AI validation was skipped.",
                    "severity": "warning",
                }
            )
            return result

        from oarepo_checks.tasks import run_llm_check

        run_llm_check.delay(
            prompt=prompt,
            record_id=str(record.id),
            config_id=str(config.id),
        )

        return result

    def parse_errors(self, llm_output: str) -> list[dict]:
        """Create error messages for the UI."""
        max_output_chars = current_app.config.get("OAREPO_CHECKS_MAX_LLM_OUTPUT_CHARS", 5000000)
        if len(llm_output) > max_output_chars:
            return []

        try:
            json_output = json.loads(llm_output)
        except json.JSONDecodeError:
            return []

        if not isinstance(json_output, dict):
            return []

        output = []

        for path, info in json_output.items():
            if not isinstance(info, dict):
                continue

            errors = info.get("errors")

            if not isinstance(errors, list) or not errors:
                continue

            valid_errors = []

            for error in errors:
                if not isinstance(error, dict):
                    continue

                valid_errors.append(
                    {
                        "error_short": str(error.get("error_short", "")),
                        "error_long": str(error.get("error_long", "")),
                        "manual_check_needed": bool(error.get("manual_check_needed", True)),
                    }
                )

            if not valid_errors:
                continue

            output.append(
                {
                    "field": path,
                    "messages": valid_errors,
                    "description": "LLM generated errors. Proceed with caution.",
                    "severity": "warning",
                }
            )

        return output
