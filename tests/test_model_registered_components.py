# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from oarepo_checks.services.components.checks import OARepoCheckComponent


def test_registered_components(model_a):
    assert OARepoCheckComponent in model_a.record_service_components
