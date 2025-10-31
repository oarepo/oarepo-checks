from invenio_checks.models import CheckRun
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_records_resources.services.uow import (
    RecordIndexOp,
    UnitOfWork,
)


def test_invenio_checks_checks_component_only(
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

    # Step 5: Add the submitter to the community as a member (curator role)
    inviter(submitter.id, community.id, "curator")

    # Step 6: Create a draft with review in parent
    service = current_rdm_records_service
    draft = service.create(submitter.identity, minimal_record)

    record = draft._record
    record.parent.communities.add(community.data["id"], default=True)

    with UnitOfWork(db.session) as uow:
        uow.register(
            ParentRecordCommitOp(record.parent, indexer_context=dict(service=service))
        )

        uow.register(RecordIndexOp(record, indexer=service.indexer, index_refresh=True))
        # assert draft.to_dict()["status"] == "draft"

    # Verify Checks
    check_runs_before = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,
    ).all()
    assert len(check_runs_before) == 0

    minimal_record["metadata"]["title"] = "Updated Title"

    draft_updated = service.update_draft(submitter.identity, draft.id, minimal_record)
    check_runs_after = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,
    ).all()
    assert len(check_runs_after) == 1
