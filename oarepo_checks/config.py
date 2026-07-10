#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Configuration for oarepo-checks."""

from __future__ import annotations

from oarepo_checks.services.components.register_check_config import (
    RegisterCheckComponent,
)

CHECKS_GENERIC_COMMUNITY = "generic-community"
"""A slug of community that is used for LLM prompt when record does not belong to a community."""

CHECKS_COMMUNITIES_SERVICE_COMPONENTS = [RegisterCheckComponent]
"""Extra components that are registered to COMMUNITIES_SERVICE_COMPONENTS.

The default (RegisterCheckComponent) will create a LLM configuration for a community
whenever it is added/modified.
"""
