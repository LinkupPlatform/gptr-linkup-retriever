"""The installed entry point makes ``RETRIEVER=linkup`` resolve in GPT Researcher."""

from types import SimpleNamespace

import pytest
from gpt_researcher.actions.retriever import get_retriever, get_retrievers
from gpt_researcher.config.config import Config

from gptr_linkup_retriever import LinkupSearch


def test_get_retriever_resolves_linkup() -> None:
    assert get_retriever("linkup") is LinkupSearch


def test_get_retrievers_mixes_linkup_and_builtin() -> None:
    from gpt_researcher.retrievers import Duckduckgo

    cfg = SimpleNamespace(retrievers=None, retriever=None)
    assert get_retrievers({"retrievers": "linkup, duckduckgo"}, cfg) == [LinkupSearch, Duckduckgo]


def test_config_accepts_linkup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RETRIEVER", "linkup")
    assert Config().retrievers == ["linkup"]
