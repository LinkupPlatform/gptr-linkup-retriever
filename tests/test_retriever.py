from types import SimpleNamespace

import pytest
from linkup import (
    LinkupClient,
    LinkupFetchResponse,
    LinkupSearchImageResult,
    LinkupSearchResults,
    LinkupSearchTextResult,
    LinkupSource,
    LinkupSourcedAnswer,
)
from pytest_mock import MockerFixture

from gptr_linkup_retriever import LinkupSearch


def _text_result(url: str, content: str = "content") -> LinkupSearchTextResult:
    return LinkupSearchTextResult(
        type="text", name="Title", url=url, content=content, favicon="https://a.example/icon"
    )


def test_api_key_from_env() -> None:
    assert LinkupSearch("q").api_key == "test-api-key"


def test_api_key_from_headers_takes_precedence() -> None:
    assert LinkupSearch("q", headers={"linkup_api_key": "header-key"}).api_key == "header-key"


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LINKUP_API_KEY")
    with pytest.raises(ValueError, match="LINKUP_API_KEY"):
        LinkupSearch("q")


def test_accepts_extra_call_site_kwargs() -> None:
    retriever = LinkupSearch("q", headers={}, query_domains=None, websocket=None, researcher=None)
    assert retriever.query == "q"


def test_depth_defaults_to_standard() -> None:
    assert LinkupSearch("q").depth == "standard"


def test_depth_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINKUP_DEPTH", "Deep")
    assert LinkupSearch("q").depth == "deep"


def test_invalid_depth_falls_back_to_standard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINKUP_DEPTH", "extreme")
    assert LinkupSearch("q").depth == "standard"


def test_search_calls_linkup(mocker: MockerFixture) -> None:
    mock = mocker.patch.object(LinkupClient, "search", return_value=LinkupSearchResults(results=[]))
    LinkupSearch("what is linkup", query_domains=["linkup.so"]).search(max_results=5)
    mock.assert_called_once_with(
        "what is linkup",
        depth="standard",
        output_type="searchResults",
        include_domains=["linkup.so"],
        max_results=5,
    )


def test_search_without_query_domains_passes_none(mocker: MockerFixture) -> None:
    mock = mocker.patch.object(LinkupClient, "search", return_value=LinkupSearchResults(results=[]))
    LinkupSearch("q", query_domains=[]).search()
    assert mock.call_args.kwargs["include_domains"] is None


def test_search_normalizes_hits(mocker: MockerFixture) -> None:
    mocker.patch.object(
        LinkupClient,
        "search",
        return_value=LinkupSearchResults(
            results=[
                _text_result("https://a.example", "body a"),
                LinkupSearchImageResult(type="image", name="img", url="https://img.example/1.png"),
                _text_result("", "orphan"),
                _text_result("https://b.example", ""),
            ]
        ),
    )
    assert LinkupSearch("q").search() == [
        {"href": "https://a.example", "body": "body a"},
        {"href": "https://b.example", "body": ""},
    ]


def test_search_caps_results(mocker: MockerFixture) -> None:
    mocker.patch.object(
        LinkupClient,
        "search",
        return_value=LinkupSearchResults(
            results=[_text_result(f"https://{i}.example") for i in range(5)]
        ),
    )
    assert len(LinkupSearch("q").search(max_results=2)) == 2


def test_search_swallows_client_errors(mocker: MockerFixture) -> None:
    mocker.patch.object(LinkupClient, "search", side_effect=RuntimeError("api down"))
    assert LinkupSearch("q").search() == []


def test_search_tolerates_unexpected_response(mocker: MockerFixture) -> None:
    mocker.patch.object(LinkupClient, "search", return_value=SimpleNamespace(results=None))
    assert LinkupSearch("q").search() == []


def test_answer(mocker: MockerFixture) -> None:
    mock = mocker.patch.object(
        LinkupClient,
        "search",
        return_value=LinkupSourcedAnswer(
            answer="Linkup is a web search API.",
            sources=[
                LinkupSource(
                    name="Linkup", url="https://www.linkup.so", snippet="snippet", favicon=""
                ),
                LinkupSource(name="Orphan", url="", snippet="x", favicon=""),
            ],
        ),
    )
    assert LinkupSearch("what is linkup").answer() == {
        "answer": "Linkup is a web search API.",
        "sources": [{"href": "https://www.linkup.so", "title": "Linkup", "body": "snippet"}],
    }
    assert mock.call_args.kwargs["output_type"] == "sourcedAnswer"


def test_fetch(mocker: MockerFixture) -> None:
    mock = mocker.patch.object(
        LinkupClient, "fetch", return_value=LinkupFetchResponse(markdown="# Title", favicon="")
    )
    assert LinkupSearch("q").fetch("https://a.example") == {
        "href": "https://a.example",
        "raw_content": "# Title",
    }
    mock.assert_called_once_with("https://a.example", render_js=False)
