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

from typing import TYPE_CHECKING

from oarepo.config.base import set_constants_in_caller

from oarepo_checks.llm_client import BaseLLMClient, ChatEInfraClient
from oarepo_checks.services.components.register_check_config import (
    RegisterCheckComponent,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

CHECKS_GENERIC_COMMUNITY = "generic-community"  # slug of the generic community
CHECKS_COMMUNITIES_SERVICE_COMPONENTS = [RegisterCheckComponent]
OAREPO_CHECKS_DEFAULT_CHAT_EINFRA_CLIENT = "chat_einfra"


def configure_llm(  # noqa: PLR0913
    api_token: str | None = None,
    *,
    enabled: bool = True,
    client_name: str = OAREPO_CHECKS_DEFAULT_CHAT_EINFRA_CLIENT,
    api_url: str = "https://llm.ai.e-infra.cz/v1/chat/completions",
    model: str = "gpt-oss-120b",
    fallback_community: str = "restricted",
    llm_clients: Mapping[str, BaseLLMClient] | None = None,
    default_client: str | None = None,
) -> None:
    """Configure OARepo checks LLM client constants in invenio.cfg."""
    CHECKS_ENABLED = enabled
    if CHECKS_ENABLED:
        OAREPO_CHECKS_LLM_CLIENTS = dict(llm_clients or {})
        OAREPO_CHECKS_DEFAULT_LLM_CLIENT = default_client
        CHECKS_GENERIC_COMMUNITY = fallback_community

        if api_token and client_name not in OAREPO_CHECKS_LLM_CLIENTS:
            OAREPO_CHECKS_LLM_CLIENTS[client_name] = ChatEInfraClient(
                api_token=api_token,
                api_url=api_url,
                model=model,
            )
            OAREPO_CHECKS_DEFAULT_LLM_CLIENT = default_client or client_name
        elif default_client is None and OAREPO_CHECKS_LLM_CLIENTS:
            OAREPO_CHECKS_DEFAULT_LLM_CLIENT = next(iter(OAREPO_CHECKS_LLM_CLIENTS))

    set_constants_in_caller(locals())
