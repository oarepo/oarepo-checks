# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for CLI commands."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from click.testing import CliRunner
from flask import Flask
from invenio_checks.models import CheckConfig
from invenio_communities import current_communities
from invenio_communities.communities.records.api import Community
from sqlalchemy.orm.attributes import flag_modified

from oarepo_checks import cli as cli_module
from oarepo_checks.cli import checks


def test_enable_llm_check_success(app, db, users, location, search_clear):
    """Test enabling LLM check for a specific community."""
    community_owner = users[0]

    # Create a community
    community_dict = {
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        },
        "slug": "test-community",
        "metadata": {
            "title": "Test Community",
            "description": "Community to test CLI.",
            "curation_policy": "Testing policy.",
            "page": "Info.",
            "website": "https://example.org/",
            "organizations": [{"name": "Test Org"}],
        },
    }

    community = current_communities.service.create(community_owner.identity, community_dict)
    Community.index.refresh()

    # Disable the auto-created LLM check
    check_config = CheckConfig.query.filter_by(
        community_id=community.id,
        check_id="llm",
    ).first()
    check_config.enabled = False
    db.session.add(check_config)
    db.session.commit()

    community_configs = CheckConfig.query.filter_by(community_id=community.id, check_id="llm").all()
    assert len(community_configs) == 1
    assert community_configs[0].enabled is False

    # Run the CLI command
    runner = CliRunner()
    result = runner.invoke(checks, ["enable-llm-check", "test-community"])

    # Check command output
    assert result.exit_code == 0
    assert "Enabled LLM check for community 'test-community'" in result.output
    assert "1 config(s) updated" in result.output

    # Verify the config is now enabled
    db.session.expire_all()
    updated_config = CheckConfig.query.filter_by(
        community_id=community.id,
        check_id="llm",
    ).first()
    assert updated_config.enabled is True


def test_disable_llm_check_success(app, db, users, location, search_clear):
    """Test disabling LLM check for a specific community."""
    community_owner = users[0]

    # Create a community
    community_dict = {
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        },
        "slug": "test-community-to-disable",
        "metadata": {
            "title": "Test Community",
            "description": "Community to test CLI.",
            "curation_policy": "Testing policy.",
            "page": "Info.",
            "website": "https://example.org/",
            "organizations": [{"name": "Test Org"}],
        },
    }

    community = current_communities.service.create(community_owner.identity, community_dict)
    Community.index.refresh()

    db.session.flush()
    db.session.expire_all()

    community_configs = CheckConfig.query.filter_by(community_id=community.id, check_id="llm").all()
    assert len(community_configs) == 1
    assert community_configs[0].enabled is True

    # Run the CLI command
    runner = CliRunner()
    result = runner.invoke(checks, ["disable-llm-check", "test-community-to-disable"])

    # Check command output
    assert result.exit_code == 0
    assert "Disabled LLM check for community 'test-community-to-disable'" in result.output
    assert "1 config(s) updated" in result.output

    # Verify the config is now enabled
    db.session.expire_all()
    updated_config = CheckConfig.query.filter_by(
        community_id=community.id,
        check_id="llm",
    ).first()
    assert updated_config.enabled is False


def test_disable_llm_check_nonexistent_community(app, db, search_clear):
    """Test disabling LLM check for a non-existent community."""
    runner = CliRunner()
    result = runner.invoke(checks, ["disable-llm-check", "nonexistent-community"])

    # Should show error message
    assert result.exit_code == 0
    assert "Error: Could not find community with slug 'nonexistent-community'" in result.output


def test_disable_llm_check_already_disabled(app, db, users, location, search_clear):
    """Test disabling LLM check that is already disabled."""
    community_owner = users[0]

    # Create a community
    community_dict = {
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        },
        "slug": "already-disabled",
        "metadata": {
            "title": "Already Disabled",
            "description": "Community with disabled check.",
            "curation_policy": "Testing policy.",
            "page": "Info.",
            "website": "https://example.org/",
            "organizations": [{"name": "Test Org"}],
        },
    }

    community = current_communities.service.create(community_owner.identity, community_dict)
    Community.index.refresh()

    # Disable the auto-created LLM check
    check_config = CheckConfig.query.filter_by(
        community_id=community.id,
        check_id="llm",
    ).first()
    check_config.enabled = False
    db.session.add(check_config)
    db.session.commit()

    # Run the CLI command again
    runner = CliRunner()
    result = runner.invoke(checks, ["disable-llm-check", "already-disabled"])

    # Should still succeed
    assert result.exit_code == 0
    assert "Disabled LLM check for community 'already-disabled'" in result.output


def test_update_prompts_all_communities(app, db, users, location, search_clear):
    """Test updating prompts for all communities."""
    community_owner = users[0]

    # Create two communities with LLM checks
    communities_data = [
        {
            "slug": "community-one",
            "title": "Community One",
            "curation_policy": "Policy for community one.",
        },
        {
            "slug": "community-two",
            "title": "Community Two",
            "curation_policy": "Policy for community two.",
        },
    ]

    created_communities = []
    for comm_data in communities_data:
        community_dict = {
            "access": {
                "visibility": "public",
                "member_policy": "open",
                "record_policy": "open",
            },
            "slug": comm_data["slug"],
            "metadata": {
                "title": comm_data["title"],
                "description": "Test community.",
                "curation_policy": comm_data["curation_policy"],
                "page": "Info.",
                "website": "https://example.org/",
                "organizations": [{"name": "Test Org"}],
            },
        }

        community = current_communities.service.create(community_owner.identity, community_dict)
        created_communities.append(community)

    Community.index.refresh()

    # Modify the auto-created prompts to something identifiable
    for community in created_communities:
        check_config = CheckConfig.query.filter_by(
            community_id=community.id,
            check_id="llm",
        ).first()
        check_config.params["prompt"] = "Old outdated prompt"
        flag_modified(check_config, "params")
        db.session.add(check_config)

    db.session.flush()

    # Run the CLI command
    runner = CliRunner()
    result = runner.invoke(checks, ["update-prompts"])

    # Check command output
    assert result.exit_code == 0
    assert "Fetching all communities..." in result.output
    assert "Community One: Updated 1 config(s)" in result.output
    assert "Community Two: Updated 1 config(s)" in result.output
    assert "Updated: 2" in result.output

    # Verify prompts were updated
    db.session.expire_all()
    for community in created_communities:
        updated_config = CheckConfig.query.filter_by(
            community_id=community.id,
            check_id="llm",
        ).first()
        assert updated_config.params["prompt"] != "Old outdated prompt"
        assert "{{record_serialized}}" in updated_config.params["prompt"]
        # Verify community-specific data is in the prompt
        community_obj = Community.pid.resolve(str(community.id))
        assert community_obj.metadata["title"] in updated_config.params["prompt"]


def test_update_prompts_specific_community(app, db, users, location, search_clear):
    """Test updating prompts for a specific community only."""
    community_owner = users[0]

    # Create two communities
    community_dict_1 = {
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        },
        "slug": "update-me",
        "metadata": {
            "title": "Update Me",
            "description": "This should be updated.",
            "curation_policy": "Update policy.",
            "page": "Info.",
            "website": "https://example.org/",
            "organizations": [{"name": "Test Org"}],
        },
    }

    community_dict_2 = {
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        },
        "slug": "dont-update",
        "metadata": {
            "title": "Don't Update",
            "description": "This should not be updated.",
            "curation_policy": "No update.",
            "page": "Info.",
            "website": "https://example.org/",
            "organizations": [{"name": "Test Org"}],
        },
    }

    community_1 = current_communities.service.create(community_owner.identity, community_dict_1)
    community_2 = current_communities.service.create(community_owner.identity, community_dict_2)
    Community.index.refresh()

    # Modify the auto-created prompts to something identifiable
    check_config_1 = CheckConfig.query.filter_by(
        community_id=community_1.id,
        check_id="llm",
    ).first()
    check_config_1.params["prompt"] = "Old prompt 1"
    flag_modified(check_config_1, "params")
    db.session.add(check_config_1)

    check_config_2 = CheckConfig.query.filter_by(
        community_id=community_2.id,
        check_id="llm",
    ).first()
    check_config_2.params["prompt"] = "Old prompt 2"
    flag_modified(check_config_2, "params")
    db.session.add(check_config_2)

    db.session.commit()

    # Run the CLI command for only one community
    runner = CliRunner()
    result = runner.invoke(checks, ["update-prompts", "--community-slug", "update-me"])

    # Check command output
    assert result.exit_code == 0
    assert "Update Me: Updated 1 config(s)" in result.output
    assert "Updated: 1" in result.output

    # Verify only the first community's prompt was updated
    db.session.expire_all()
    updated_config_1 = CheckConfig.query.filter_by(
        community_id=community_1.id,
        check_id="llm",
    ).first()
    assert updated_config_1.params["prompt"] != "Old prompt 1"
    assert "Update Me" in updated_config_1.params["prompt"]

    # The second community should still have the old prompt
    updated_config_2 = CheckConfig.query.filter_by(
        community_id=community_2.id,
        check_id="llm",
    ).first()
    assert updated_config_2.params["prompt"] == "Old prompt 2"


def test_cli_enable(monkeypatch):
    app = Flask("test")
    commits = []
    added = []
    config = SimpleNamespace(enabled=False)
    community = {"id": "community-id", "metadata": {"title": "Community"}}

    monkeypatch.setattr(
        cli_module,
        "current_communities",
        SimpleNamespace(service=SimpleNamespace(search=lambda identity, params=None: SimpleNamespace(hits=[community]))),
    )
    monkeypatch.setattr(
        cli_module,
        "CheckConfig",
        SimpleNamespace(query=SimpleNamespace(filter_by=lambda **kwargs: SimpleNamespace(all=lambda: [config]))),
    )
    monkeypatch.setattr(
        cli_module,
        "db",
        SimpleNamespace(session=SimpleNamespace(add=lambda value: added.append(value), commit=lambda: commits.append(True))),
    )

    with app.app_context():
        result = CliRunner().invoke(checks, ["enable-llm-check", "community"])

    assert result.exit_code == 0
    assert "Enabled LLM check for community 'community' (1 config(s) updated)" in result.output
    assert config.enabled is True

    with app.app_context():
        result = CliRunner().invoke(checks, ["disable-llm-check", "community"])

    assert result.exit_code == 0
    assert "Disabled LLM check for community 'community' (1 config(s) updated)" in result.output
    assert config.enabled is False
    assert added == [config, config]
    assert len(commits) == 2


def test_cli_no_community(monkeypatch):
    app = Flask("test")

    monkeypatch.setattr(
        cli_module,
        "current_communities",
        SimpleNamespace(service=SimpleNamespace(search=lambda identity, params=None: SimpleNamespace(hits=[]))),
    )

    with app.app_context():
        result = CliRunner().invoke(checks, ["disable-llm-check", "missing"])

    assert result.exit_code == 0
    assert "Error: Could not find community with slug 'missing'" in result.output

    monkeypatch.setattr(
        cli_module,
        "current_communities",
        SimpleNamespace(service=SimpleNamespace(search=lambda identity, params=None: SimpleNamespace(hits=[{"id": "id"}]))),
    )
    monkeypatch.setattr(
        cli_module,
        "CheckConfig",
        SimpleNamespace(query=SimpleNamespace(filter_by=lambda **kwargs: SimpleNamespace(all=lambda: []))),
    )

    with app.app_context():
        result = CliRunner().invoke(checks, ["enable-llm-check", "without-check"])

    assert result.exit_code == 0
    assert "No LLM check found for community 'without-check'" in result.output


def test_cli_update_prompts(monkeypatch):
    app = Flask("test")
    commits = []
    added = []
    flagged = []
    community_one = {"id": "one", "metadata": {"title": "Community One"}}
    community_two = {"id": "two", "metadata": {"title": "Community Two"}}
    config_one = SimpleNamespace(params={"prompt": "old one"})
    config_two = SimpleNamespace(params={"prompt": "old two"})

    monkeypatch.setattr(
        cli_module,
        "current_communities",
        SimpleNamespace(
            service=SimpleNamespace(
                search=lambda identity, params=None: SimpleNamespace(
                    hits=[community_one] if params else [community_one, community_two]
                )
            )
        ),
    )
    monkeypatch.setattr(
        cli_module,
        "CheckConfig",
        SimpleNamespace(
            query=SimpleNamespace(
                filter_by=lambda **kwargs: SimpleNamespace(
                    all=lambda: [config_one] if kwargs["community_id"] == "one" else [config_two]
                )
            )
        ),
    )
    monkeypatch.setattr(
        cli_module,
        "db",
        SimpleNamespace(session=SimpleNamespace(add=lambda value: added.append(value), commit=lambda: commits.append(True))),
    )
    monkeypatch.setattr(cli_module, "flag_modified", lambda value, field: flagged.append((value, field)))
    monkeypatch.setattr(
        cli_module,
        "create_prompt",
        lambda record_serialized, language, community: f"prompt for {community['metadata']['title']}",
    )

    with app.app_context():
        result = CliRunner().invoke(checks, ["update-prompts"])

    assert result.exit_code == 0
    assert "Fetching all communities..." in result.output
    assert "Community One: Updated 1 config(s)" in result.output
    assert "Community Two: Updated 1 config(s)" in result.output
    assert "Updated: 2" in result.output
    assert config_one.params["prompt"] == "prompt for Community One"
    assert config_two.params["prompt"] == "prompt for Community Two"

    with app.app_context():
        result = CliRunner().invoke(checks, ["update-prompts", "--community-slug", "community-one"])

    assert result.exit_code == 0
    assert "Community One: Updated 1 config(s)" in result.output
    assert "Updated: 1" in result.output
    assert added == [config_one, config_two, config_one]
    assert flagged == [(config_one, "params"), (config_two, "params"), (config_one, "params")]
    assert len(commits) == 2
