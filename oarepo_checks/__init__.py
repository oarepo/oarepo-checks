#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

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
