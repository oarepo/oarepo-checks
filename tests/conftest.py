#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-checks (see https://github.com/oarepo/oarepo-checks).
#
# oarepo-checks is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Pytest configuration and fixtures for oarepo-checks tests."""

from __future__ import annotations

import contextlib
import sys
from typing import Any

import pytest
from invenio_access.permissions import (
    system_identity,
)
from invenio_app.factory import create_api
from invenio_checks.models import CheckConfig, Severity
from invenio_communities import current_communities
from invenio_communities.communities.records.api import Community
from invenio_communities.communities.services.components import DefaultCommunityComponents
from invenio_rdm_records import config
from invenio_rdm_records.proxies import current_rdm_records_service
from invenio_rdm_records.services.communities.components import (
    CommunityServiceComponents,
)
from invenio_rdm_records.services.components import DefaultRecordsComponents
from invenio_rdm_records.services.permissions import RDMRequestsPermissionPolicy
from invenio_records_resources.references.entity_resolvers import ServiceResultResolver
from invenio_users_resources.proxies import current_users_service
from invenio_vocabularies.proxies import current_service as vocabulary_service
from invenio_vocabularies.records.api import Vocabulary
from werkzeug.local import LocalProxy

from oarepo_checks.services.components.checks import OARepoCheckComponent
from oarepo_checks.services.components.register_check_config import RegisterCheckComponent

from .dummy_llm_client import DummyClient


@pytest.fixture(autouse=True)
def _mock_invenio_url_for(monkeypatch) -> None:
    """Replace `invenio_url_for` with a no-op mock that returns a simple string.

    invenio_url_for is not neccessary here and it was the easiest fix to avoid errors
    """

    def _fake_invenio_url_for(endpoint, **values: Any) -> str:
        # return something deterministic and safe for tests
        try:
            return f"/mock-url/{endpoint}"
        except Exception:  # noqa: BLE001
            return "/mock-url/"

    # Patch the helper module if present
    with contextlib.suppress(Exception):
        import invenio_base.urls.helpers as _helpers

        monkeypatch.setattr(_helpers, "invenio_url_for", _fake_invenio_url_for, raising=False)

    # Patch the package-level symbol if present
    with contextlib.suppress(Exception):
        import invenio_base as _ib

        monkeypatch.setattr(_ib, "invenio_url_for", _fake_invenio_url_for, raising=False)

    # Also overwrite the name in any already-imported module that defines it
    for _mod in list(sys.modules.values()):
        if not _mod:
            continue

        if hasattr(_mod, "invenio_url_for"):
            with contextlib.suppress(Exception):
                # best-effort patching only
                monkeypatch.setattr(_mod, "invenio_url_for", _fake_invenio_url_for, raising=False)


pytest_plugins = [
    "pytest_oarepo.requests.fixtures",
    "pytest_oarepo.records",
    "pytest_oarepo.fixtures",
    "pytest_oarepo.users",
    "pytest_oarepo.files",
]


@pytest.fixture(scope="module")
def app_config(app_config):
    """Override pytest-invenio app_config fixture.

    For test purposes we need to enforce the configuration variables set in
    config.py. Because invenio-rdm-records is not a flavour extension, it does
    not enforce them via a config entrypoint or ext.py; only flavour
    extensions are allowed to forcefully set configuration.

    This means there is a clash between configuration set by
    invenio-records-rest and this module for instance. We want this module's
    config.py to apply in tests.
    """
    supported_configurations = [
        "FILES_REST_PERMISSION_FACTORY",
        "PIDSTORE_RECID_FIELD",
        "RECORDS_PERMISSIONS_RECORD_POLICY",
        "RECORDS_REST_ENDPOINTS",
        "REQUESTS_PERMISSION_POLICY",
    ]

    for config_key in supported_configurations:
        app_config[config_key] = getattr(config, config_key, None)

    app_config["THEME_SITENAME"] = "Invenio"

    app_config["RECORDS_REFRESOLVER_CLS"] = "invenio_records.resolver.InvenioRefResolver"
    app_config["RECORDS_REFRESOLVER_STORE"] = "invenio_jsonschemas.proxies.current_refresolver_store"

    records_index = LocalProxy(lambda: current_rdm_records_service.record_cls.index._name)  # noqa: SLF001
    app_config["OAISERVER_RECORD_INDEX"] = records_index
    app_config["INDEXER_DEFAULT_INDEX"] = records_index

    # Variable not used. We set it to silent warnings
    app_config["JSONSCHEMAS_HOST"] = "not-used"

    app_config["DATACITE_ENABLED"] = False

    # Custom fields
    app_config["RDM_NAMESPACES"] = {
        "cern": "https://home.cern/",
    }

    # Storage classes
    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
        "F": "Fetch",
        "R": "Remote",
    }
    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"

    # Specifying a notifications settings view function to trigger registration of route
    # needed for invenio_url_for
    app_config["NOTIFICATIONS_SETTINGS_VIEW_FUNCTION"] = lambda: "<index>"

    # Communities
    app_config["COMMUNITIES_SERVICE_COMPONENTS"] = CommunityServiceComponents

    # Specifying default resolvers. Will only be used in specific test cases.
    app_config["NOTIFICATIONS_ENTITY_RESOLVERS"] = [
        ServiceResultResolver(service_id="users", type_key="user"),
        ServiceResultResolver(service_id="communities", type_key="community"),
        ServiceResultResolver(service_id="requests", type_key="request"),
        ServiceResultResolver(service_id="request_events", type_key="request_event"),
    ]

    # Disable the automatic creation of moderation requests after publishing a record.
    # When testing unverified users, there is a "unverified_user" fixture for that purpose.
    app_config["ACCOUNTS_DEFAULT_USERS_VERIFIED"] = True
    app_config["RDM_USER_MODERATION_ENABLED"] = False
    app_config["REQUESTS_PERMISSION_POLICY"] = RDMRequestsPermissionPolicy

    app_config["COMMUNITIES_OAI_SETS_PREFIX"] = "community-"

    app_config["CHECKS_ENABLED"] = True
    app_config["OAREPO_CHECKS_LLM_CLIENTS"] = {"dummy": DummyClient()}
    app_config["OAREPO_CHECKS_DEFAULT_LLM_CLIENT"] = "dummy"

    modified_records_components = DefaultRecordsComponents
    for i, component in enumerate(modified_records_components):
        if component.__name__ == "ChecksComponent":
            # Replace with our custom component
            modified_records_components[i] = OARepoCheckComponent

    app_config["RDM_RECORDS_SERVICE_COMPONENTS"] = modified_records_components
    app_config["CHECKS_GENERIC_COMMUNITY"] = "generic-community"  # slug of the generic community
    app_config["COMMUNITIES_SERVICE_COMPONENTS"] = [*DefaultCommunityComponents, RegisterCheckComponent]

    app_config["CELERY_TASK_ALWAYS_EAGER"] = True
    app_config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://invenio:invenio@localhost:5432/invenio"
    return app_config


@pytest.fixture(scope="module")
def extra_entry_points():
    """Extra entrypoints."""
    return {
        "invenio_base.blueprints": [
            "invenio_app_rdm_records = tests.mock_module:create_invenio_app_rdm_records_blueprint",
            "invenio_app_rdm_requests = tests.mock_module:create_invenio_app_rdm_requests_blueprint",
            "invenio_app_rdm_communities = tests.mock_module:create_invenio_app_rdm_communities_blueprint",
        ],
        "invenio_base.apps": [
            "invenio_rdm_records = invenio_rdm_records:InvenioRDMRecords",
        ],
        "invenio_base.api_apps": [
            "invenio_rdm_records = invenio_rdm_records:InvenioRDMRecords",
        ],
    }


@pytest.fixture
def minimal_record():
    """Minimal record data as dict coming from the external world."""
    return {
        "pids": {},
        "access": {
            "record": "public",
            "files": "public",
        },
        "files": {
            "enabled": False,  # Most tests don't care about files
        },
        "metadata": {
            "creators": [
                {
                    "person_or_org": {
                        "family_name": "Brown",
                        "given_name": "Troy",
                        "type": "personal",
                    }
                },
                {
                    "person_or_org": {
                        "name": "Troy Inc.",
                        "type": "organizational",
                    },
                },
            ],
            "publication_date": "2020-06-01",
            # because DATACITE_ENABLED is True, this field is required
            "publisher": "Acme Inc",
            "resource_type": {"id": "image-photo"},
            "title": "A Romans story",
        },
    }


@pytest.fixture
def index_users():
    """Index users for an up-to-date user service."""

    def _index() -> None:
        current_users_service.indexer.process_bulk_queue()
        current_users_service.record_cls.index.refresh()

    return _index


@pytest.fixture
def inviter(index_users):
    """Add/invite a user to a community with a specific role."""

    def invite(user_id: str, community_id: str, role: str) -> None:
        """Add/invite a user to a community with a specific role."""
        assert role in ["curator", "owner"]
        invitation_data = {
            "members": [
                {
                    "type": "user",
                    "id": user_id,
                }
            ],
            "role": role,
            "visible": True,
        }
        current_communities.service.members.add(system_identity, community_id, invitation_data)
        index_users()

    return invite


@pytest.fixture
def resource_type_v(app, db, resource_type_type):
    """Resource type vocabulary record."""
    vocabulary_service.create(
        system_identity,
        {
            "id": "dataset",
            "icon": "table",
            "props": {
                "csl": "dataset",
                "datacite_general": "Dataset",
                "datacite_type": "",
                "openaire_resourceType": "21",
                "openaire_type": "dataset",
                "eurepo": "info:eu-repo/semantics/other",
                "schema.org": "https://schema.org/Dataset",
                "subtype": "",
                "type": "dataset",
                "marc21_type": "dataset",
                "marc21_subtype": "",
            },
            "title": {"en": "Dataset"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    vocabulary_service.create(
        system_identity,
        {  # create base resource type
            "id": "image",
            "props": {
                "csl": "figure",
                "datacite_general": "Image",
                "datacite_type": "",
                "openaire_resourceType": "25",
                "openaire_type": "dataset",
                "eurepo": "info:eu-repo/semantics/other",
                "schema.org": "https://schema.org/ImageObject",
                "subtype": "",
                "type": "image",
                "marc21_type": "image",
                "marc21_subtype": "",
            },
            "icon": "chart bar outline",
            "title": {"en": "Image"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    vocabulary_service.create(
        system_identity,
        {  # create base resource type
            "id": "software",
            "props": {
                "csl": "figure",
                "datacite_general": "Software",
                "datacite_type": "",
                "openaire_resourceType": "0029",
                "openaire_type": "software",
                "eurepo": "info:eu-repo/semantics/other",
                "schema.org": "https://schema.org/SoftwareSourceCode",
                "subtype": "",
                "type": "image",
                "marc21_type": "software",
                "marc21_subtype": "",
            },
            "icon": "code",
            "title": {"en": "Software"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    vocab = vocabulary_service.create(
        system_identity,
        {
            "id": "image-photo",
            "props": {
                "csl": "graphic",
                "datacite_general": "Image",
                "datacite_type": "Photo",
                "openaire_resourceType": "25",
                "openaire_type": "dataset",
                "eurepo": "info:eu-repo/semantics/other",
                "schema.org": "https://schema.org/Photograph",
                "subtype": "image-photo",
                "type": "image",
                "marc21_type": "image",
                "marc21_subtype": "photo",
            },
            "icon": "chart bar outline",
            "title": {"en": "Photo"},
            "tags": ["depositable", "linkable"],
            "type": "resourcetypes",
        },
    )

    Vocabulary.index.refresh()

    return vocab


@pytest.fixture
def create_metadata_check(db, community):
    check_config = CheckConfig(
        community_id=community.id,
        check_id="metadata",  # The ID of the MetadataCheck
        severity=Severity.WARN,
        enabled=True,
        params={
            "rules": [
                {
                    "id": "title-required",
                    "title": "Title Required",
                    "message": "A title is required for all records",
                    "level": "failure",
                    "checks": [{"type": "field", "path": "metadata.title"}],
                }
            ]
        },
    )
    db.session.add(check_config)
    db.session.commit()


@pytest.fixture
def create_generic_community_metadata_check(db, generic_community):
    check_config = CheckConfig(
        community_id=generic_community.id,
        check_id="metadata",  # The ID of the MetadataCheck
        severity=Severity.WARN,
        enabled=True,
        params={
            "rules": [
                {
                    "id": "title-required",
                    "title": "Title Required",
                    "message": "A title is required for all records",
                    "level": "failure",
                    "checks": [{"type": "field", "path": "metadata.title"}],
                }
            ]
        },
    )
    db.session.add(check_config)
    db.session.commit()


@pytest.fixture
def create_llm_check(db, community):
    check_config_llm = CheckConfig(
        community_id=community.id,
        check_id="llm",  # The ID of the LLMCheck
        severity=Severity.WARN,
        enabled=True,
        params={"prompt": "Default prompt"},
    )
    db.session.add(check_config_llm)
    db.session.commit()


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return create_api


@pytest.fixture
def resource_type_type(app, db):
    """Resource type vocabulary type."""
    return vocabulary_service.create_type(system_identity, "resourcetypes", "rsrct")


@pytest.fixture
def community(db, users):
    community_owner = users[0]

    community_dict = {
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        },
        "slug": "test_community_check_failure",
        "metadata": {
            "title": "Test Community for Check Failure",
            "description": "Community to test check failures.",
            "curation_policy": "Testing.",
            "page": "Info.",
            "website": "https://example.org/",
            "organizations": [{"name": "Test Org"}],
        },
    }
    community = current_communities.service.create(community_owner.identity, community_dict)
    Community.index.refresh()
    return community


@pytest.fixture
def generic_community(db, users):
    community_owner = users[0]

    community_dict = {
        "access": {
            "visibility": "public",
            "member_policy": "open",
            "record_policy": "open",
        },
        "slug": "generic-community",
        "metadata": {
            "title": "Generic Community",
            "description": "A generic community for testing purposes.",
            "curation_policy": "Testing.",
            "page": "Info.",
            "website": "https://example.org/",
            "organizations": [{"name": "Generic Test Org"}],
        },
    }
    community = current_communities.service.create(community_owner.identity, community_dict)
    Community.index.refresh()
    return community
