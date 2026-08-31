# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

from __future__ import annotations

from types import SimpleNamespace

from oarepo_checks.ui import components as ui_components


def test_ui_errors_component(monkeypatch):
    expired = []
    api_record = {"api": "record"}
    api_record_obj = {"record": "object"}
    record = {"errors": ["existing error"]}
    run = SimpleNamespace(
        result={
            "errors": [
                {
                    "field": "metadata.title",
                    "messages": [
                        {"error_long": "Long error"},
                        {"error_short": "Short error"},
                    ],
                }
            ]
        }
    )

    monkeypatch.setattr(ui_components, "record_from_result", lambda value: api_record_obj)
    monkeypatch.setattr(ui_components, "ChecksAPI", SimpleNamespace(get_runs=lambda value: [run]))
    monkeypatch.setattr(
        ui_components,
        "db",
        SimpleNamespace(session=SimpleNamespace(expire=lambda value, fields: expired.append((value, fields)))),
    )

    assert ui_components.normalize_check_error(
        {
            "field": "metadata.description",
            "messages": [{"error": "Description error"}],
        }
    ) == {
        "field": "metadata.description",
        "messages": ["Description error"],
    }

    ui_components.ChecksUIErrorsComponent(None).before_ui_edit(api_record=api_record, record=record)

    assert expired == [(run, ["result", "status", "state"])]
    assert record["errors"] == [
        "existing error",
        {
            "field": "metadata.title",
            "messages": ["Long error", "Short error"],
        },
    ]
