# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-rdm (see https://github.com/oarepo/oarepo-rdm).
#
# oarepo-rdm is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import Any, ClassVar

from flask import Blueprint
from invenio_records_permissions.generators import AnyUser, Generator
from oarepo_model.api import model
from oarepo_model.customizations import (
    SetPermissionPolicy,
)
from oarepo_model.presets.drafts import drafts_preset
from oarepo_model.presets.records_resources import records_resources_preset
from oarepo_runtime.services.config import EveryonePermissionPolicy

from oarepo_checks.model.presets import check_preset


class PermissionPolicyWithModelAPermission(EveryonePermissionPolicy):
    """Permission policy that adds permissions for testing."""

    can_draft_create_files: ClassVar[list[Generator]] = [
        AnyUser(),
    ]

    can_draft_set_content_files: ClassVar[list[Generator]] = [
        AnyUser(),
    ]

    can_draft_commit_files: ClassVar[list[Generator]] = [
        AnyUser(),
    ]

    can_draft_get_content_files: ClassVar[list[Generator]] = [
        AnyUser(),
    ]

    get_content_files: ClassVar[list[Generator]] = [
        AnyUser(),
    ]
    can_create_files: ClassVar[list[Generator]] = [
        AnyUser(),
    ]


modela = model(
    "modela",
    version="1.0.0",
    presets=[
        records_resources_preset,
        drafts_preset,
        check_preset,
    ],
    configuration={"ui_blueprint_name": "modela_ui"},
    types=[
        {
            "Metadata": {
                "properties": {
                    "title": {"type": "fulltext+keyword"},
                    "adescription": {"type": "keyword"},
                },
            },
        }
    ],
    metadata_type="Metadata",
    customizations=[SetPermissionPolicy(PermissionPolicyWithModelAPermission)],
)
modela.register()


def create_modela_ui_blueprint(app):
    bp = Blueprint("modela_ui", __name__)

    # mock UI resource
    @bp.route("/modela_ui/preview/<pid_value>", methods=["GET"])
    def preview(pid_value: str) -> str:
        return "preview ok"

    @bp.route("/modela_ui/record_detail/<pid_value>", methods=["GET"])
    def record_detail(pid_value: str) -> str:
        return "preview ok"

    @bp.route("/modela_ui/record_latest/<pid_value>", methods=["GET"])
    def record_latest(pid_value: str) -> str:
        return "latest ok"

    @bp.route("/modela_ui/search", methods=["GET"])
    def search() -> str:
        return "search ok"

    @bp.route("/modela_ui/deposit_edit/<pid_value>", methods=["GET"])
    def deposit_edit(pid_value: str, *args: Any, **kwargs: Any) -> str:
        return "deposit_edit ok"

    return bp


def create_app_rdm_blueprint(app):
    blueprint = Blueprint(
        "invenio_app_rdm_records",
        __name__,
    )

    def record_file_download(pid_value, file_item=None, is_preview=False, **kwargs):  # noqa: ANN003, ANN202
        """Fake record_file_download view function."""
        return "<file content>"

    def record_detail(pid_value, file_item=None, is_preview=False, **kwargs):  # noqa: ANN003, ANN202
        """Fake record_detail view function."""
        return "<record detail>"

    def deposit_edit(pid_value, file_item=None, is_preview=False, **kwargs):  # noqa: ANN003, ANN202
        """Fake record_detail view function."""
        return "<deposit edit>"

    def record_latest(record=None, **kwargs):  # noqa: ANN003, ANN202
        """Fake record_latest view function."""
        return "<record latest>"

    def record_from_pid(record=None, **kwargs):  # noqa: ANN003, ANN202
        """Fake record_from_pid view function."""
        return "<record from pid>"

    # Records URL rules
    blueprint.add_url_rule(
        "/records/<pid_value>/files/<path:filename>",
        view_func=record_file_download,
    )

    blueprint.add_url_rule(
        "/records/<pid_value>",
        view_func=record_detail,
    )

    blueprint.add_url_rule(
        "/uploads/<pid_value>",
        view_func=deposit_edit,
    )

    blueprint.add_url_rule(
        "/records/<pid_value>/latest",
        view_func=record_latest,
    )

    blueprint.add_url_rule(
        "/<any(doi):pid_scheme>/<path:pid_value>",
        view_func=record_from_pid,
    )

    return blueprint
