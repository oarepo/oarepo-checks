# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Checks proxies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import current_app
from werkzeug.local import LocalProxy

if TYPE_CHECKING:
    from oarepo_checks.ext import OARepoChecks

    current_oarepo_checks: OARepoChecks  # type: ignore[reportRedeclaration]

# note: mypy does not understand LocalProxy[OARepoChecks], so we type it as OARepoChecks
# and ignore the redeclaration error
current_oarepo_checks = LocalProxy(lambda: current_app.extensions["oarepo-checks"])  # type: ignore[assignment]
