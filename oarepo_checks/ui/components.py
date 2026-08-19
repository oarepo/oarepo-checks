#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""OARepo UI components for rendering stored check results in deposit forms."""

from __future__ import annotations

from typing import Any

from invenio_checks.api import ChecksAPI
from invenio_db import db
from oarepo_runtime.typing import record_from_result
from oarepo_ui.resources.components.base import UIResourceComponent

from oarepo_checks.utils import check_error_messages


def normalize_check_error(error: dict[str, Any]) -> dict[str, Any]:
    """Normalize errors for the deposit form."""
    return {
        **error,
        "messages": check_error_messages(error.get("messages", [])),
    }


class ChecksUIErrorsComponent(UIResourceComponent):
    """Inject stored check run errors into the edit form initial record data."""

    def before_ui_edit(self, *, api_record: Any, record: dict, **kwargs: Any) -> None:
        """Add async check errors to record.errors before the form is rendered."""
        _ = kwargs
        check_errors: list = []
        api_record_obj = record_from_result(api_record)

        runs = list(ChecksAPI.get_runs(api_record_obj))

        for run in runs:
            db.session.expire(run, ["result", "status", "state"])
            result = dict(run.result or {})

            check_errors.extend(normalize_check_error(error) for error in result.get("errors") or [])

        if check_errors:
            record.setdefault("errors", [])
            record["errors"].extend(check_errors)
