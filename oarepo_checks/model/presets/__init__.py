# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Init module for presets package."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .checks_preset import CheckServiceComponentPreset

if TYPE_CHECKING:
    from oarepo_model.api import FunctionalPreset
    from oarepo_model.presets import Preset

check_preset: list[type[Preset | FunctionalPreset]] = [
    CheckServiceComponentPreset,
]

__all__ = ("check_preset",)
