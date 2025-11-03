#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from unittest.mock import patch

from invenio_checks.models import CheckRun
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_records_resources.services.uow import (
    RecordIndexOp,
    UnitOfWork,
)


@patch("oarepo_checks.services.components.checks_components.ChecksComponent.create")
def test_run_checks_on_create(
    mock_create,
    app,
    db,
    location,
    users,
    community,
    minimal_record,
    inviter,
    resource_type_v,
    create_metadata_check,
    # create_llm_check,
):
    """Test that invenio-checks runs validation on community submission."""
    submitter = users[1]

    # Add the submitter to the community as a member (e.g. curator role), so he can create records in it
    inviter(submitter.id, community.id, "curator")

    # Create a draft
    service = current_rdm_records_service

    _ = service.create(submitter.identity, minimal_record)

    # Assert components has been called
    mock_create.assert_called_once()


def test_checks_on_draft_update_no_llm(
    app,
    db,
    location,
    users,
    community,
    minimal_record,
    inviter,
    resource_type_v,
    create_metadata_check,
    # create_llm_check,
):
    """Test that invenio-checks runs validation on community submission."""
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

    # Verify Checks in Database after update, should be only 1 since no LLM check
    check_runs_after = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,  # noqa: SLF001
    ).all()
    assert len(check_runs_after) == 1


def test_checks_on_draft_update_multiple_checks(
    app,
    db,
    location,
    users,
    community,
    minimal_record,
    inviter,
    resource_type_v,
    create_metadata_check,
    create_llm_check,
):
    """Test that invenio-checks runs validation on community submission."""
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

    # Verify Checks in Database after update, should be 2 since both Metadata and LLM checks
    check_runs_after = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,  # noqa: SLF001
    ).all()
    assert len(check_runs_after) == 2
