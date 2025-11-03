#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Mock test module.

It has to exist here to be picked up correctly by the create_app of
tests/resources/conftest.py .

Taken from invenio_rdm_records mock module (https://github.com/inveniosoftware/invenio-rdm-records/tree/master/tests/mock_module).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from flask import Blueprint

if TYPE_CHECKING:
    from flask import Flask


def create_invenio_app_rdm_records_blueprint(app: Flask) -> Blueprint:
    """Create fake invenio_app_rdm_records Blueprint akin to invenio-app-rdm's."""
    blueprint = Blueprint(
        "invenio_app_rdm_records",
        __name__,
    )

    def record_file_download(pid_value, file_item=None, is_preview=False, **kwargs: Any) -> str:
        """Fake record_file_download view function."""
        return "<file content>"

    def record_detail(pid_value, file_item=None, is_preview=False, **kwargs: Any) -> str:
        """Fake record_detail view function."""
        return "<record detail>"

    def deposit_edit(pid_value, file_item=None, is_preview=False, **kwargs: Any) -> str:
        """Fake record_detail view function."""
        return "<deposit edit>"

    def record_latest(record=None, **kwargs: Any) -> str:
        """Fake record_latest view function."""
        return "<record latest>"

    def record_from_pid(record=None, **kwargs: Any) -> str:
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


def verify_access_request_token() -> str:
    """Fake verifiy_access_request_token view function.

    Notice lack of parameters to test querystring injection.
    """
    return "<verification>"


def create_invenio_app_rdm_requests_blueprint(app: Flask) -> Blueprint:
    """Create fake invenio_app_rdm_requests Blueprint akin to invenio-app-rdm's."""
    blueprint = Blueprint(
        "invenio_app_rdm_requests",
        __name__,
    )

    # Requests URL rules
    blueprint.add_url_rule("/access/requests/confirm", view_func=verify_access_request_token)

    return blueprint


def create_invenio_app_rdm_communities_blueprint(app: Flask) -> Blueprint:
    """Create fake invenio_app_rdm_communities Blueprint akin to invenio-app-rdm's."""
    blueprint = Blueprint(
        "invenio_app_rdm_communities",
        __name__,
    )

    def communities_home(pid_value, community, community_ui) -> str:
        return "<communities home>"

    # Requests URL rules
    blueprint.add_url_rule("/communities/<pid_value>/", view_func=communities_home)

    return blueprint
