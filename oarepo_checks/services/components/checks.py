#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Component that runs checks on record with no communities."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, cast

from flask import current_app
from invenio_access.permissions import system_identity
from invenio_checks.api import ChecksAPI
from invenio_checks.components import ChecksComponent
from invenio_communities import current_communities

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records import Record

logger = logging.getLogger("oarepo_checks")


class OARepoCheckComponent(ChecksComponent):
    """Component that extends invenio-checks component.

    This components extends ChecksComponent by running checks on creation of records
    and overrides method for community retrieval to return a generic community in order
    to run checks even when no community is assigned to the record.
    """

    # NOTE: This class extend ChecksComponent from invenio-checks package.and it does not override
    # the whole functionality. Because of that and geeneric_community return in _get_record_communities
    # record will sometimes run checks twice instead of once (like you think on set community only).
    # This is because the original method from parent class also fetches all previous runs of
    # record from database and gets of all communities from them.
    #
    # This will be equivalent to creating record without a community,
    # run checks with generic community and then add record to the community.
    #
    # This is not a problem for now and it easily can be fixed (by overriding) in future if needed

    def create(
        self,
        identity: Identity,
        data: dict[str, Any] | None = None,
        record: Record | None = None,
        **kwargs: Any,
    ) -> None:
        """Skip checks when record is created."""

    def update_draft(
        self,
        identity: Identity,
        data: dict[str, Any] | None = None,
        record: Record | None = None,
        errors: list | None = None,
        **kwargs: Any,
    ) -> None:
        """Skip checks when a draft is updated."""
        past_runs = ChecksAPI.get_runs(record)
        if not past_runs:
            return
        logger.info("Running checks for draft update on record %s", record["id"] if record else None)
        super().update_draft(identity, data, record, errors, **kwargs)

    def edit(
        self,
        identity: Identity,
        draft: Record | None = None,
        record: Record | None = None,
        **kwargs: Any,
    ) -> None:
        """Skip checks when record is edited."""
        past_runs = ChecksAPI.get_runs(record) + ChecksAPI.get_runs(draft)
        if not past_runs:
            return

        logger.info("Running checks for edit metadata on record %s", record["id"] if record else None)
        super().edit(identity, draft, record, **kwargs)

    def submit_record(
        self,
        identity: Identity,
        data: dict[str, Any] | None = None,
        record: Record | None = None,
        **kwargs: Any,
    ) -> None:
        """Run checks on draft create."""
        _, _, _ = data, identity, kwargs
        draft = record  # rename for clarity

        # Take into account already included communities
        community_ids = self._get_record_communities(draft)

        updated_runs = []
        configs = ChecksAPI.get_configs(community_ids)
        logger.info(
            "Running checks for submit_record on record %s, community_ids=%s, configs=%s",
            record["id"] if record else None,
            community_ids,
            configs,
        )
        for config in configs:
            run = ChecksAPI.run_check(config, draft, self.uow)
            logger.info("Running check %s, result=%s", config, run)
            if run:
                updated_runs.append(run)

    def publish(
        self,
        identity: Identity,
        draft: Record | None = None,
        record: Record | None = None,
        **kwargs: Any,
    ) -> None:
        """Skip checks when record is published."""

    def _get_record_communities(self, record_or_draft: Record | None) -> set[str]:
        """Override method to return generic community when no community is present on record."""
        communities = cast("set", super()._get_record_communities(record_or_draft))
        if communities:
            return communities

        generic_community_slug = current_app.config.get("CHECKS_GENERIC_COMMUNITY")

        if generic_community_slug is None:
            return set()

        results = list(
            current_communities.service.search(system_identity, params={"q": f"slug:{generic_community_slug}"}).hits
        )

        generic_community = results[0] if results else None
        if not generic_community:
            return set()  # generic community not found
        return {generic_community["id"]}
