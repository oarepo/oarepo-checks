#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for CLI commands."""

from __future__ import annotations

from click.testing import CliRunner
from invenio_checks.models import CheckConfig
from invenio_communities import current_communities
from invenio_communities.communities.records.api import Community
from sqlalchemy.orm.attributes import flag_modified

from oarepo_checks.cli import checks


def test_enable_llm_check_success(app, db, users, location):
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
    assert updated_config.enabled is False


def test_disable_llm_check_success(app, db, users, location):
    """Test disabling LLM check for a specific community."""
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

    community_configs = CheckConfig.query.filter_by(community_id=community.id, check_id="llm").all()
    assert len(community_configs) == 1
    assert community_configs[0].enabled is True

    # Run the CLI command
    runner = CliRunner()
    result = runner.invoke(checks, ["disable-llm-check", "test-community"])

    # Check command output
    assert result.exit_code == 0
    assert "Disabled LLM check for community 'test-community'" in result.output
    assert "1 config(s) updated" in result.output

    # Verify the config is now enabled
    db.session.expire_all()
    updated_config = CheckConfig.query.filter_by(
        community_id=community.id,
        check_id="llm",
    ).first()
    assert updated_config.enabled is False


def test_disable_llm_check_nonexistent_community(app, db):
    """Test disabling LLM check for a non-existent community."""
    runner = CliRunner()
    result = runner.invoke(checks, ["disable-llm-check", "nonexistent-community"])

    # Should show error message
    assert result.exit_code == 0
    assert "Error: Could not find community with slug 'nonexistent-community'" in result.output


def test_disable_llm_check_already_disabled(app, db, users, location):
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


def test_update_prompts_all_communities(app, db, users, location):
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

    db.session.commit()
    db.session.expire_all()

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


def test_update_prompts_specific_community(app, db, users, location):
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
