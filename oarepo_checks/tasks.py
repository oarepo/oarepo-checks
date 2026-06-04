#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Celery tasks for oarepo-checks."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from celery import shared_task
from flask import current_app
from invenio_checks.contrib.metadata.check import CheckResult
from invenio_checks.models import CheckRun, CheckRunStatus
from invenio_db import db

from oarepo_checks.checks.llm_check import LLMCheck
from oarepo_checks.proxies import current_oarepo_checks


def _find_check_run(
    *,
    record_id: str,
    config_id: str,
) -> CheckRun | None:
    """Find the check run created by the synchronous request path."""
    return CheckRun.query.filter_by(  # there will always be only max one run for each config and record id combo
        config_id=uuid.UUID(config_id),
        record_id=uuid.UUID(record_id),
    ).one_or_none()


@shared_task(
    ignore_result=True,
    max_retries=5,
    autoretry_for=(TimeoutError,),
    retry_backoff=True,
)
def run_llm_check(
    *,
    prompt: str,
    record_id: str,
    config_id: str,
) -> None:
    """Run the LLM call and overwrite an already stored CheckRun."""
    run = _find_check_run(
        record_id=record_id,
        config_id=config_id,
    )

    if run is None:
        raise run_llm_check.retry(countdown=5)

    run.status = CheckRunStatus.RUNNING
    run.start_time = datetime.now(UTC)
    run.state = {"message": "LLM check is running"}
    db.session.add(run)
    db.session.commit()

    try:
        json_with_errors = current_oarepo_checks.llm_client.chat_completion(prompt)  # type: ignore[union-attr]
        errors = LLMCheck().parse_errors(json_with_errors)

        result = CheckResult(LLMCheck.id)
        result.errors.extend(errors)

        run.status = CheckRunStatus.COMPLETED
        run.end_time = datetime.now(UTC)
        run.state = ""
        run.result = result.to_dict()

        db.session.add(run)
        db.session.commit()

    except Exception:
        db.session.rollback()
        run = _find_check_run(
            record_id=record_id,
            config_id=config_id,
        )
        if run is not None:
            run.status = CheckRunStatus.ERROR
            run.end_time = datetime.now(UTC)
            run.state = {"error": "Async LLM check failed"}
            db.session.add(run)
            db.session.commit()

        current_app.logger.exception(
            "Error running async LLM check task.",
            extra={"check_config_id": config_id, "record_id": record_id},
        )
        raise
