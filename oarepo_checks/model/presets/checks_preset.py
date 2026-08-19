# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Preset to add checks service component to record service."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_model.customizations import AddToList
from oarepo_model.presets import Preset

from oarepo_checks.services.components.checks import OARepoCheckComponent

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.customizations import Customization
    from oarepo_model.model import InvenioModel


class CheckServiceComponentPreset(Preset):
    """Add checks service component to record service.

    Due to the code in runtime, it should replace original checks component, because new one inherits from it.
    """

    modifies = ("record_service_components",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddToList("record_service_components", OARepoCheckComponent)
