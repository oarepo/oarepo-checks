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

from typing import TYPE_CHECKING, Any, cast

from flask import current_app
from invenio_access.permissions import system_identity
from invenio_checks.api import ChecksAPI
from invenio_checks.components import ChecksComponent
from invenio_communities import current_communities

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records import Record


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
        identity: Identity,  # noqa: ARG002
        data: dict[str, Any] | None = None,  # noqa: ARG002
        record: Record | None = None,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        """Run checks on draft create."""
        draft = record  # rename for clarity

        # Take into account already included communities
        community_ids = self._get_record_communities(draft)

        updated_runs = []
        configs = ChecksAPI.get_configs(community_ids)
        for config in configs:
            run = ChecksAPI.run_check(config, draft, self.uow)
            if run:
                updated_runs.append(run)

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
