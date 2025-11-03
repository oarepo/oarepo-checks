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

from typing import TYPE_CHECKING

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
        self.llm_clients: dict[str, BaseLLMClient] = app.config.get("OAREPO_CHECKS_LLM_CLIENTS", {})
        self.default_llm_client: str | None = app.config.get("OAREPO_CHECKS_DEFAULT_LLM_CLIENT", None)
        app.extensions["oarepo-checks"] = self

    @property
    def llm_client(self) -> BaseLLMClient | None:
        """Get LLM client by name or default."""
        if self.default_llm_client is None:
            return None

        return self.llm_clients.get(self.default_llm_client)

    @property
    def available_llm_clients(self) -> dict[str, BaseLLMClient]:
        """Get available LLM clients."""
        return self.llm_clients
