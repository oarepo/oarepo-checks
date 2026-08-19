# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""OARepo Checks package."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .checks.llm_check import LLMCheck
from .services.components.checks import OARepoCheckComponent
from .services.components.register_check_config import RegisterCheckComponent
from .utils import create_prompt

try:
    __version__ = version("oarepo-checks")
except PackageNotFoundError:
    __version__ = "0.0.0dev0+unknown"

__all__ = (
    "LLMCheck",
    "OARepoCheckComponent",
    "RegisterCheckComponent",
    "__version__",
    "create_prompt",
)
