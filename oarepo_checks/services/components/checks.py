#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Componenent that runs checks on record creation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_checks.api import ChecksAPI
from invenio_checks.components import toggle_on_feature_flag
from invenio_drafts_resources.services.records.components import ServiceComponent

if TYPE_CHECKING:
    from flask_principal import Identity
    from invenio_records import Record


@toggle_on_feature_flag
class ChecksOnCreateComponent(ServiceComponent):
    """Checks component to run checks also on creation of a record."""

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

        past_runs = ChecksAPI.get_runs(draft)
        for run in past_runs:
            community_ids.add(str(run.config.community_id))

        updated_runs = []
        configs = ChecksAPI.get_configs(community_ids)
        for config in configs:
            run = ChecksAPI.run_check(config, draft, self.uow)
            if run:
                updated_runs.append(run)

    def _get_record_communities(self, record_or_draft: Record | None) -> set[str]:
        """Get community IDs from the record or draft.

        Taken from ChecksComponent (https://github.com/inveniosoftware/invenio-checks/blob/master/invenio_checks/components.py).
        Since we do not need to inherit from that class here, we duplicate the method.
        """
        if record_or_draft is None:
            return set()

        community_ids = set()
        for community in record_or_draft.parent.communities:  # type: ignore[attr-defined]
            community_ids.add(str(community.id))
            if community.parent:
                community_ids.add(str(community.parent.id))
        return community_ids
