# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from time import sleep
from types import SimpleNamespace

import pytest
from invenio_checks.components import ChecksComponent
from invenio_checks.models import CheckRun
from invenio_communities import current_communities
from invenio_communities.communities.records.api import Community
from invenio_rdm_records.proxies import current_rdm_records_service

from oarepo_checks.services.components import checks as checks_module
from oarepo_checks.services.components.checks import OARepoCheckComponent


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


def test_generic_community(monkeypatch):
    calls = []
    monkeypatch.setattr(ChecksComponent, "_get_record_communities", lambda self, record: set())
    monkeypatch.setattr(checks_module, "current_app", SimpleNamespace(config={"CHECKS_GENERIC_COMMUNITY": "generic"}))
    monkeypatch.setattr(
        checks_module,
        "current_communities",
        SimpleNamespace(
            service=SimpleNamespace(
                search=lambda identity, params: (
                    calls.append(("search", params)) or SimpleNamespace(hits=[{"id": "generic-community-id"}])
                )
            )
        ),
    )

    component = OARepoCheckComponent(None)

    assert component._get_record_communities({"id": "record-id"}) == {"generic-community-id"}
    assert calls == [("search", {"q": "slug:generic"})]


def test_submit_record(monkeypatch):
    calls = []
    record = {"id": "record-id"}
    monkeypatch.setattr(OARepoCheckComponent, "_get_record_communities", lambda self, record: {"community-id"})
    monkeypatch.setattr(
        checks_module,
        "ChecksAPI",
        SimpleNamespace(
            get_configs=lambda community_ids: calls.append(("get_configs", community_ids)) or ["config-1", "config-2"],
            run_check=lambda config, draft, uow: calls.append(("run_check", config, draft, uow)) or f"run-{config}",
        ),
    )

    component = OARepoCheckComponent(None)
    component.uow = "uow"

    component.submit_record(identity=None, data={}, record=record)

    assert calls == [
        ("get_configs", {"community-id"}),
        ("run_check", "config-1", record, "uow"),
        ("run_check", "config-2", record, "uow"),
    ]


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
        CheckRun.record_id == draft._record.id,
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
        CheckRun.record_id == draft._record.id,
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
        CheckRun.record_id == draft._record.id,
    ).all()
    assert len(check_runs_after) == 1
    assert str(check_runs_after[0].config.community_id) == generic_community.id
    assert check_runs_after[0].result["success"]
    end_time_after = check_runs_after[0].end_time
    assert end_time_after > end_time_before
