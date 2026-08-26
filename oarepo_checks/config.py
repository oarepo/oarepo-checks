# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Configuration for oarepo-checks."""

from __future__ import annotations

from oarepo_checks.services.components.register_check_config import (
    RegisterCheckComponent,
)

CHECKS_GENERIC_COMMUNITY = "generic-community"
"""A slug of community that is used for LLM prompt when record does not belong to a community."""

OAREPO_CHECKS_MAX_LLM_INPUT_CHARS = 2000000
"""Maximum rendered LLM prompt size in characters."""

OAREPO_CHECKS_MAX_LLM_OUTPUT_CHARS = 5000000
"""Maximum LLM response size in characters."""

CHECKS_COMMUNITIES_SERVICE_COMPONENTS = [RegisterCheckComponent]
"""Extra components that are registered to COMMUNITIES_SERVICE_COMPONENTS.

The default (RegisterCheckComponent) will create a LLM configuration for a community
whenever it is added/modified.
"""
