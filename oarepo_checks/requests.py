#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Request customizations for oarepo-checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import current_app
from invenio_access.permissions import system_identity
from invenio_checks.api import ChecksAPI
from invenio_communities import current_communities
from oarepo_requests.actions.publish_draft import PublishDraftSubmitAction

if TYPE_CHECKING:
    from typing import Any

    from flask_principal import Identity
    from invenio_records.api import Record
    from invenio_records_resources.services.uow import UnitOfWork  # type: ignore[reportAttributeAccessIssue]


def _get_generic_community_ids() -> set[str]:
    generic_community_slug = current_app.config.get("CHECKS_GENERIC_COMMUNITY")
    if generic_community_slug is None:
        return set()

    results = list(
        current_communities.service.search(system_identity, params={"q": f"slug:{generic_community_slug}"}).hits
    )
    return {results[0]["id"]} if results else set()


def _run_llm_check(record: Record, uow: UnitOfWork) -> None:
    configs = ChecksAPI.get_configs(_get_generic_community_ids())
    for config in configs:
        if config.check_id == "llm":
            ChecksAPI.run_check(config, record, uow)


class LLMPublishDraftSubmitAction(PublishDraftSubmitAction):
    """Submit action that starts the LLM check for publish draft requests."""

    def apply(
        self,
        identity: Identity,
        uow: UnitOfWork,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Run the LLM check before applying the publish draft submit action."""
        _run_llm_check(self.topic, uow)
        super().apply(identity, uow, *args, **kwargs)
