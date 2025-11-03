#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Checks proxies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask import current_app
from werkzeug.local import LocalProxy

if TYPE_CHECKING:
    from oarepo_checks.ext import OARepoChecks

    current_oarepo_checks: OARepoChecks  # type: ignore[reportRedeclaration]

# note: mypy does not understand LocalProxy[OARepoRuntime], so we type it as OARepoRuntime
# and ignore the redeclaration error
current_oarepo_checks = LocalProxy(lambda: current_app.extensions["oarepo-checks"])  # type: ignore[assignment]
