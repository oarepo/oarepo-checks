#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from invenio_checks.models import CheckRun
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_records_resources.services.uow import (
    RecordIndexOp,
    UnitOfWork,
)

from oarepo_checks.requests import _run_llm_check


def test_do_not_run_checks_on_draft_update(
    app,
    db,
    location,
    users,
    community,
    minimal_record,
    inviter,
    resource_type_v,
    create_metadata_check,
    search_clear,
):
    """Test that invenio-checks does not run validation on draft update."""
    submitter = users[1]

    # Add the submitter to the community as a member (e.g. curator role), so he can create records in it
    inviter(submitter.id, community.id, "curator")

    # Create a draft
    service = current_rdm_records_service
    draft = service.create(submitter.identity, minimal_record)

    # Add community to the parent record
    record = draft._record  # noqa: SLF001
    record.parent.communities.add(community.data["id"], default=True)
    with UnitOfWork(db.session) as uow:
        uow.register(ParentRecordCommitOp(record.parent, indexer_context={"service": service}))

        uow.register(RecordIndexOp(record, indexer=service.indexer, index_refresh=True))

    # Verify Checks in Database before update
    check_runs_before = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,  # noqa: SLF001
    ).all()
    assert len(check_runs_before) == 0

    # Update draft
    minimal_record["metadata"]["title"] = "Updated Title"
    _ = service.update_draft(submitter.identity, draft.id, minimal_record)

    check_runs_after = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,  # noqa: SLF001
    ).all()

    assert len(check_runs_after) == 0


def test_run_llm_check_in_background_on_submit_to_community(
    app,
    db,
    location,
    users,
    community,
    minimal_record,
    resource_type_v,
    search_clear,
    monkeypatch,
):
    """Test that LLM check is queued only when submitting a draft to a community."""
    submitter = users[1]

    app.config["CHECKS_GENERIC_COMMUNITY"] = community.data["slug"]
    service = current_rdm_records_service
    draft = service.create(submitter.identity, minimal_record)
    record = draft._record  # noqa: SLF001

    check_runs_before = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,  # noqa: SLF001
    ).all()
    assert len(check_runs_before) == 0

    with UnitOfWork(db.session) as uow:
        _run_llm_check(record, uow)

    check_runs_after = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,  # noqa: SLF001
    ).all()

    assert len(check_runs_after) == 1
    assert check_runs_after[0].config.check_id == "llm"
    assert str(check_runs_after[0].config.community_id) == community.id
