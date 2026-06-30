#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Component that creates/updates CheckConfig on community create/update."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from invenio_checks.models import CheckConfig, Severity
from invenio_db import db
from invenio_drafts_resources.services.records.components import ServiceComponent
from sqlalchemy.orm.attributes import flag_modified

from oarepo_checks.utils import create_prompt

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records import Record

logger = logging.getLogger("oarepo_checks")


class RegisterCheckComponent(ServiceComponent):
    """Component that adds ChecksConfig on community create/update actions.

    When a community is created CheckConfig is created for LLM check with a generated prompt with
    additional information about the community. On community update the prompt is regenerated
    to reflect the updated community information.
    """

    def _create_prompt_for_community(self, community: Record | None) -> str:
        """Generate a prompt for the given community.

        :param community: Community record

        :return: Generated prompt with community-specific rules
        """
        # Create prompt with community data
        # Use placeholder for record_serialized since it will be replaced at check time
        return create_prompt(
            record_serialized="{{record_serialized}}",
            language="{{language}}",
            community=community,
        )

    def create(
        self,
        identity: Identity,  # noqa: ARG002
        data: dict | None = None,  # noqa: ARG002
        record: Record | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Run on community create."""
        community = record  # rename for clarity

        logger.info("Creating check config for community %s", community)

        # Generate the prompt with community-specific information
        prompt = self._create_prompt_for_community(community)

        if community:
            # Store the generated prompt
            check_config_llm = CheckConfig(
                community_id=community.id,  # Community ID where to add check to
                check_id="llm",  # State that we would like to use the LLM check
                severity=Severity.WARN,
                enabled=True,
                params={"prompt": prompt},
            )

            db.session.add(check_config_llm)
            logger.info("Check config for community %s added to the database", community)

    def update(
        self,
        identity: Identity,  # noqa: ARG002
        data: dict | None = None,  # noqa: ARG002
        record: Record | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Run on community update."""
        community = record  # rename for clarity

        logger.info("Updating check config for community %s", community)

        existing_configs = []

        if community:
            existing_configs = CheckConfig.query.filter_by(
                community_id=community.id,
                check_id="llm",
            ).all()

        if not existing_configs:
            # Create new config with generated prompt
            prompt = self._create_prompt_for_community(community)
            check_config_llm = CheckConfig(
                community_id=community.id,  # type: ignore[union-attr]
                check_id="llm",
                severity=Severity.WARN,
                enabled=True,
                params={"prompt": prompt},
            )
            db.session.add(check_config_llm)
            logger.info("Check config for community %s updated", community)

        for existing_config in existing_configs:
            # Regenerate prompt with updated community data
            prompt = self._create_prompt_for_community(community)
            existing_config.params["prompt"] = prompt
            # Mark the JSON field as modified so SQLAlchemy detects the change
            flag_modified(existing_config, "params")
            db.session.add(existing_config)
            logger.info("Check config for community %s updated", community)
