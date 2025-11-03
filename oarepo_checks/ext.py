# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 CERN.
#
# Invenio-Checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio checks application."""


class OARepoChecks(object):
    """ORepo-Checks extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.llm_clients = app.config.get("OAREPO_CHECKS_LLM_CLIENTS", {})
        self.default_llm_client = app.config.get(
            "OAREPO_CHECKS_DEFAULT_LLM_CLIENT", None
        )
        app.extensions["oarepo-checks"] = self

    @property
    def llm_client(self, name=None):
        """Get LLM client by name or default."""
        if name is None:
            name = self.default_llm_client
        return self.llm_clients.get(name)

    @property
    def available_llm_clients(self):
        """Get available LLM clients."""
        return self.llm_clients


def finalize_app(app):
    """Finalize the application."""

    pass
