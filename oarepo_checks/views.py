# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Views module."""

from __future__ import annotations

from flask import Blueprint

bp = Blueprint("oarepo_checks", __name__, template_folder="templates")
