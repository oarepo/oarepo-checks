#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""CLI commands for oarepo-checks."""

from __future__ import annotations

import click
from flask.cli import with_appcontext
from invenio_access.permissions import system_identity
from invenio_checks.models import CheckConfig
from invenio_communities import current_communities
from invenio_db import db
from sqlalchemy.orm.attributes import flag_modified

from oarepo_checks.utils import create_prompt


@click.group()
def checks() -> None:
    """OARepo Checks management commands."""


@checks.command("disable-llm-check")
@click.argument("community_slug")
@with_appcontext
def disable_llm_check(community_slug: str) -> None:
    """Disable LLM check for a specific community.

    :param community_slug: The slug of the community to disable LLM check for
    Example:
        oarepo checks disable-llm-check my-community

    """
    changed_state = False

    # Find the community by slug
    results = list(current_communities.service.search(system_identity, params={"q": f"slug:{community_slug}"}).hits)
    community_id = results[0]["id"] if results else None
    if not community_id:
        click.secho(
            f"Error: Could not find community with slug '{community_slug}'",
            fg="red",
        )
        return

    # Find the LLM check config for this community
    check_configs = CheckConfig.query.filter_by(
        community_id=community_id,
        check_id="llm",
    ).all()

    if not check_configs:
        click.secho(
            f"No LLM check found for community '{community_slug}'",
            fg="yellow",
        )
        return

    # Disable all LLM check configs for this community
    for config in check_configs:
        if config.enabled:
            config.enabled = False
            db.session.add(config)
            changed_state = True

    if changed_state:
        db.session.commit()

    click.secho(
        f"Disabled LLM check for community '{community_slug}' ({len(check_configs)} config(s) updated)",
        fg="green",
    )


@checks.command("enable-llm-check")
@click.argument("community_slug")
@with_appcontext
def enable_llm_check(community_slug: str) -> None:
    """Enable LLM check for a specific community.

    :param community_slug: The slug of the community to enable LLM check for
    Example:
        oarepo checks enable-llm-check my-community

    """
    changed_state = False

    # Find the community by slug
    results = list(current_communities.service.search(system_identity, params={"q": f"slug:{community_slug}"}).hits)
    community_id = results[0]["id"] if results else None
    if not community_id:
        click.secho(
            f"Error: Could not find community with slug '{community_slug}'",
            fg="red",
        )
        return

    # Find the LLM check config for this community
    check_configs = CheckConfig.query.filter_by(
        community_id=community_id,
        check_id="llm",
    ).all()

    if not check_configs:
        click.secho(
            f"No LLM check found for community '{community_slug}'",
            fg="yellow",
        )
        return

    # Enable all LLM check configs for this community
    for config in check_configs:
        if not config.enabled:
            config.enabled = True
            db.session.add(config)
            changed_state = True
    if changed_state:
        db.session.commit()

    click.secho(
        f"Enabled LLM check for community '{community_slug}' ({len(check_configs)} config(s) updated)",
        fg="green",
    )


@checks.command("update-prompts")
@click.option(
    "--community-slug",
    default=None,
    help="Update prompts only for a specific community (by slug)",
)
@with_appcontext
def update_prompts(community_slug: str | None = None) -> None:
    """Update LLM check prompts for all communities or a specific community.

    This regenerates the prompts with the latest templates and community data.

    :param community_slug: Optional slug to update only one community

    Example:
        oarepo checks update-prompts
        oarepo checks update-prompts --community-slug my-community

    """
    # Get communities to process
    if community_slug:
        results = list(current_communities.service.search(system_identity, params={"q": f"slug:{community_slug}"}).hits)
        communities = [results[0] if results else None]
        if not communities[0]:
            click.secho(
                f"Error: Could not find community with slug '{community_slug}'",
                fg="red",
            )
            return
    else:
        # Get all communities
        click.echo("Fetching all communities...")
        communities = list(current_communities.service.search(system_identity).hits)
        click.echo(f"Found {len(communities)} communities")

    click.echo()

    updated_count = 0
    skipped_count = 0
    error_count = 0

    for community in communities:
        community_title = (community or {}).get("metadata", {}).get("title", "Unknown")
        community_id = (community or {}).get("id")

        # Find LLM check configs for this community
        check_configs = CheckConfig.query.filter_by(
            community_id=community_id,
            check_id="llm",
        ).all()

        if not check_configs:
            click.secho(f"      {community_title}: No LLM check config found", fg="dim")
            skipped_count += 1
            continue

        try:
            # Generate new prompt
            new_prompt = create_prompt(
                record_serialized="{{record_serialized}}",
                language="{{language}}",
                community=community,
            )

            for config in check_configs:
                config.params["prompt"] = new_prompt
                # Mark the JSON field as modified so SQLAlchemy detects the change
                flag_modified(config, "params")
                db.session.add(config)

                updated_count += 1

            click.secho(
                f"      {community_title}: Updated {len(check_configs)} config(s)",
                fg="green",
            )

        except Exception as e:  # noqa: BLE001
            click.secho(
                f"      {community_title}: Error - {e}",
                fg="red",
            )
            error_count += 1

    if updated_count > 0:
        db.session.commit()

    # Print summary
    click.echo()
    click.secho("Summary:", bold=True)
    click.echo(f"  Updated: {updated_count}")
    click.echo(f"  Skipped: {skipped_count}")
    if error_count > 0:
        click.secho(f"  Errors:  {error_count}", fg="red")
