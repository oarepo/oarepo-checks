#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Utility functions for oarepo-checks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from flask import render_template

if TYPE_CHECKING:
    from invenio_communities.communities.records.api import Community


def check_error_messages(messages: list[Any]) -> list[str]:
    """Convert check messages to the list[str] shape expected by deposit forms."""
    normalized_messages = []
    for message in messages or []:
        if isinstance(message, str):
            normalized_messages.append(message)
            continue

        if isinstance(message, dict):
            text = (
                message.get("message")
                or message.get("error")
                or message.get("error_long")
                or message.get("error_short")
            )
            normalized_messages.append(str(text or message))
            continue

        normalized_messages.append(str(message))
    return normalized_messages


def create_prompt(
    record_serialized: str,
    community: Community | dict | None = None,
    repository_rules_template: str = "oarepo_checks/repository_rules.jinja2",
    community_rules_template: str = "oarepo_checks/community_rules.jinja2",
    prompt_template: str = "oarepo_checks/llm_prompt.jinja2",
    **extra_context: Any,
) -> str:
    """Create a prompt for LLM check from Jinja templates.

    This function renders a complete LLM prompt by combining:
    1. Repository-wide rules (apply to all records)
    2. Community-specific rules (apply to records in a specific community)
    3. The main prompt template that structures the LLM request

    :param record_serialized: Serialized record data (usually JSON string)
    :param community: Community object or dict containing community metadata.
                      If provided, community-specific rules will be included.
    :param repository_rules_template: Path to the repository rules Jinja template
    :param community_rules_template: Path to the community rules Jinja template
    :param prompt_template: Path to the main prompt Jinja template
    :param extra_context: Additional context variables to pass to templates

    :return: Rendered prompt ready to send to LLM

    Example:
        >>> from invenio_communities.proxies import (
        ...     current_communities,
        ... )
        >>> community = (
        ...     current_communities.service.read(
        ...         identity, community_id
        ...     )
        ... )
        >>> prompt = create_prompt(
        ...     record_serialized='{"metadata": {...}}',
        ...     community=community._record,
        ... )

    """
    # Render repository rules
    repository_rules = render_template(repository_rules_template, **extra_context)

    # Render community rules (with community object if provided)
    community_rules = render_template(
        community_rules_template,
        community=community,
        **extra_context,
    )

    # Render final prompt that combines everything
    return cast(
        "str",
        render_template(
            prompt_template,
            record_serialized=record_serialized,
            repository_rules=repository_rules,
            community_rules=community_rules,
            community=community,
            **extra_context,
        ),
    )
