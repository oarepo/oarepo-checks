#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from time import sleep

import pytest
from invenio_checks.models import CheckRun
from invenio_communities import current_communities
from invenio_communities.communities.records.api import Community
from invenio_rdm_records.proxies import current_rdm_records_service


def test_create_check_config_on_community_create(app, db, users, location, search_clear):
    """Test that CheckConfig is created on community creation."""
    community_owner = users[0]

    community_dict = {
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        },
        "slug": "test",
        "metadata": {
            "title": "Test Community",
            "description": "Community to test.",
            "curation_policy": "Testing policy description.",
            "page": "Info.",
            "website": "https://example.org/",
            "organizations": [{"name": "Test Org"}],
        },
    }

    community = current_communities.service.create(community_owner.identity, community_dict)

    Community.index.refresh()

    # Verify that CheckConfig for LLM check is created
    from invenio_checks.models import CheckConfig

    check_config_llm = CheckConfig.query.filter_by(
        community_id=community.id,
        check_id="llm",
    ).first()

    assert check_config_llm is not None
    assert str(check_config_llm.community_id) == str(community.id)
    assert check_config_llm.enabled
    assert check_config_llm.severity.name == "WARN"
    assert "Testing policy description." in check_config_llm.params["prompt"]


def test_create_check_config_on_community_update(app, db, users, location, search_clear):
    """Test that CheckConfig is updated on community update."""
    community_owner = users[0]

    community_dict = {
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        },
        "slug": "test",
        "metadata": {
            "title": "Test Community",
            "description": "Community to test.",
            "curation_policy": "Testing policy description.",
            "page": "Info.",
            "website": "https://example.org/",
            "organizations": [{"name": "Test Org"}],
        },
    }

    community = current_communities.service.create(community_owner.identity, community_dict)
    Community.index.refresh()

    # Verify that CheckConfig for LLM check is created
    from invenio_checks.models import CheckConfig

    check_config_llm = CheckConfig.query.filter_by(
        community_id=community.id,
        check_id="llm",
    ).first()

    assert str(check_config_llm.community_id) == str(community.id)
    assert "Testing policy description." in check_config_llm.params["prompt"]

    community_dict["metadata"]["curation_policy"] = "Updated policy description."
    _ = current_communities.service.update(community_owner.identity, community.id, community_dict)
    Community.index.refresh()

    check_config_llm = CheckConfig.query.filter_by(
        community_id=community.id,
        check_id="llm",
    ).first()
    assert str(check_config_llm.community_id) == str(community.id)
    assert "Updated policy description." in check_config_llm.params["prompt"]


@pytest.mark.skip("Problems with DB fixture that keeps old data between tests")
def test_run_checks_on_record_create_with_no_community(
    app,
    db,
    location,
    users,
    community,
    generic_community,
    minimal_record,
    inviter,
    resource_type_v,
    search_clear,
):
    """Test that invenio-checks runs check on record creation with no community."""
    submitter = users[1]

    # Create a draft
    service = current_rdm_records_service
    draft = service.create(submitter.identity, minimal_record)

    check_runs_after = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,  # noqa: SLF001
    ).all()
    assert len(check_runs_after) == 1
    assert str(check_runs_after[0].config.community_id) == generic_community.id
    assert check_runs_after[0].result["success"]


@pytest.mark.skip("Problems with DB fixture that keeps old data between tests")
def test_run_checks_on_record_update_with_no_community(
    app,
    db,
    location,
    users,
    generic_community,
    minimal_record,
    inviter,
    resource_type_v,
    search_clear,
):
    """Test that invenio-checks runs check on record creation with no community."""
    submitter = users[1]

    # Create a draft
    service = current_rdm_records_service
    draft = service.create(submitter.identity, minimal_record)

    check_runs_before = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,  # noqa: SLF001
    ).all()
    end_time_before = check_runs_before[0].end_time
    assert len(check_runs_before) == 1
    assert str(check_runs_before[0].config.community_id) == generic_community.id
    assert check_runs_before[0].result["success"]

    sleep(1)  # Ensure end_time is different

    minimal_record["metadata"]["title"] = "Updated Title"
    _ = service.update_draft(submitter.identity, draft.id, minimal_record)

    # It should be updated run
    check_runs_after = CheckRun.query.filter(
        CheckRun.record_id == draft._record.id,  # noqa: SLF001
    ).all()
    assert len(check_runs_after) == 1
    assert str(check_runs_after[0].config.community_id) == generic_community.id
    assert check_runs_after[0].result["success"]
    end_time_after = check_runs_after[0].end_time
    assert end_time_after > end_time_before
