#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Dummy LLM client for tests."""

from __future__ import annotations

from typing import Any

from oarepo_checks.llm_client import BaseLLMClient


class DummyClient(BaseLLMClient):
    """Client for chat.ai.e-infra.cz API."""

    def chat_completion(
        self,
        prompt: str,  # noqa: ARG002
        **kwargs: Any,  # noqa: ARG002
    ) -> str:
        """Get chat completion from the LLM."""
        return """{
    "metadata.title": {
        "section_empty": false,
        "errors": [
            {
                "error_short": "Název je příliš obecný a neodráží obsah obrázku/fotografie",
                "error_long": "Název 'Updated Title' je nedostatečně popisný pro typ záznamu 'image-photo'. Doporučujeme upravit název tak, aby specifikoval obsah obrázku (např. 'Fotografie krajiny X z roku 2020').",
                "manual_check_needed": false
            }
        ]
    },
    "license": {
        "section_empty": false,
        "errors": [
            {
                "error_short": "Chybí licence pro veřejný záznam",
                "error_long": "Záznam má nastaveno 'access.record: public', ale chybí specifikace licence. Doporučujeme doplnit licenci (např. Creative Commons CC-BY 4.0) pro jasné určení podmínek užití.",
                "manual_check_needed": false
            }
        ]
    }
}"""  # noqa: E501
