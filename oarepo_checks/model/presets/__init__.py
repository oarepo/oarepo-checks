#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
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
