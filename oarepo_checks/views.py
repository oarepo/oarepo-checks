#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Views module."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import Blueprint

if TYPE_CHECKING:
    from flask import Flask


def create_blueprint(app: Flask) -> Blueprint:
    """Create the OARepo Checks blueprint to register templates, menu and filters."""
    blueprint = Blueprint("oarepo_checks", __name__, template_folder="templates")
    blueprint.app_context_processor(lambda: ({"current_app": app}))
    return blueprint
