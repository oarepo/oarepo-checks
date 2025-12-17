#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""OARepo checks flask extension."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from .views import bp

if TYPE_CHECKING:
    from flask import Flask

    from oarepo_checks.llm_client import BaseLLMClient


class OARepoChecks:
    """OARepo-Checks extension."""

    def __init__(self, app: Flask | None = None) -> None:
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Flask application initialization."""
        self.app = app
        app.register_blueprint(bp)
        self.init_config(app)

        app.extensions["oarepo-checks"] = self

    def init_config(self, app: Flask) -> None:
        """Initilize checks config."""
        from invenio_communities.communities.services.components import DefaultCommunityComponents

        from . import config

        app.config.setdefault("CHECKS_GENERIC_COMMUNITY", config.CHECKS_GENERIC_COMMUNITY)
        app.config.setdefault("COMMUNITIES_SERVICE_COMPONENTS", [*DefaultCommunityComponents]).extend(
            config.CHECKS_COMMUNITIES_SERVICE_COMPONENTS
        )

    @property
    def llm_client(self) -> BaseLLMClient | None:
        """Get defautl LLM client."""
        default_client = self.app.config.get("OAREPO_CHECKS_DEFAULT_LLM_CLIENT", None)
        return self.available_llm_clients.get(default_client, None) if default_client else None

    @property
    def available_llm_clients(self) -> dict[str, BaseLLMClient]:
        """Get available LLM clients."""
        return cast("dict[str, BaseLLMClient]", self.app.config.get("OAREPO_CHECKS_LLM_CLIENTS", {}))
