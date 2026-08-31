# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from oarepo_checks import tasks
from oarepo_checks.checks import llm_check as llm_check_module


def test_filter(monkeypatch):
    record_id = uuid.uuid4()
    config_id = uuid.uuid4()

    class Query:
        def filter_by(self, **kwargs):
            self.kwargs = kwargs
            return self

        def one_or_none(self):
            return "check-run"

    query = Query()
    monkeypatch.setattr(tasks, "CheckRun", SimpleNamespace(query=query))

    assert tasks._find_check_run(record_id=str(record_id), config_id=str(config_id)) == "check-run"
    assert query.kwargs == {"record_id": record_id, "config_id": config_id}


def test_llm_check_update(monkeypatch):
    run = SimpleNamespace()
    commits = []
    prompts = []

    session = SimpleNamespace(
        add=lambda obj: None,
        commit=lambda: commits.append(True),
        rollback=lambda: None,
    )

    def chat_completion(prompt):
        prompts.append(prompt)
        return '{"metadata.title": {"errors": [{"error_short": "Bad title"}]}}'

    monkeypatch.setattr(tasks, "_find_check_run", lambda **kwargs: run)
    monkeypatch.setattr(tasks, "db", SimpleNamespace(session=session))
    monkeypatch.setattr(
        tasks, "current_oarepo_checks", SimpleNamespace(llm_client=SimpleNamespace(chat_completion=chat_completion))
    )
    monkeypatch.setattr(llm_check_module, "current_app", SimpleNamespace(config={}))

    tasks.run_llm_check.run(prompt="prompt", record_id=str(uuid.uuid4()), config_id=str(uuid.uuid4()))

    assert run.status == tasks.CheckRunStatus.COMPLETED
    assert run.state == ""
    assert run.result["errors"][0]["field"] == "metadata.title"
    assert prompts == ["prompt"]


def test_llm_check_failure(monkeypatch):
    run = SimpleNamespace()
    commits = []
    rollbacks = []

    session = SimpleNamespace(
        add=lambda obj: None,
        commit=lambda: commits.append(True),
        rollback=lambda: rollbacks.append(True),
    )

    def chat_completion(prompt):
        raise RuntimeError("LLM failed")

    monkeypatch.setattr(tasks, "_find_check_run", lambda **kwargs: run)
    monkeypatch.setattr(tasks, "db", SimpleNamespace(session=session))
    monkeypatch.setattr(
        tasks, "current_oarepo_checks", SimpleNamespace(llm_client=SimpleNamespace(chat_completion=chat_completion))
    )
    monkeypatch.setattr(
        tasks, "current_app", SimpleNamespace(logger=SimpleNamespace(exception=lambda *args, **kwargs: None))
    )

    with pytest.raises(RuntimeError, match="LLM failed"):
        tasks.run_llm_check.run(prompt="prompt", record_id=str(uuid.uuid4()), config_id=str(uuid.uuid4()))

    assert run.status == tasks.CheckRunStatus.ERROR
    assert run.state == {"error": "Async LLM check failed"}
    assert len(commits) == 2
    assert len(rollbacks) == 1


def test_llm_check_skip(monkeypatch):
    run = SimpleNamespace()
    commits = []

    session = SimpleNamespace(
        add=lambda obj: None,
        commit=lambda: commits.append(True),
        rollback=lambda: None,
    )

    monkeypatch.setattr(tasks, "_find_check_run", lambda **kwargs: run)
    monkeypatch.setattr(tasks, "db", SimpleNamespace(session=session))
    monkeypatch.setattr(tasks, "current_oarepo_checks", SimpleNamespace(llm_client=None))

    tasks.run_llm_check.run(
        prompt="prompt",
        record_id=str(uuid.uuid4()),
        config_id=str(uuid.uuid4()),
    )

    assert run.status == tasks.CheckRunStatus.COMPLETED
    assert run.result["errors"] == []
    assert len(commits) == 1
