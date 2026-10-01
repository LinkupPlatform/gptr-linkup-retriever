"""Linkup search retriever for GPT Researcher."""

from __future__ import annotations

import logging
import os
from typing import Any, Literal, cast

from gpt_researcher.retrievers.base import BaseRetriever
from linkup import LinkupClient, LinkupSearchResults, LinkupSearchTextResult, LinkupSourcedAnswer

logger = logging.getLogger(__name__)

Depth = Literal["flash", "fast", "standard", "deep"]

_DEPTHS: tuple[str, ...] = ("flash", "fast", "standard", "deep")
_DEFAULT_DEPTH: Depth = "standard"


class LinkupSearch(BaseRetriever):
    """
    Linkup API Retriever

    Searches the web in real time with Linkup and returns relevant, citable sources. Select it
    in GPT Researcher with ``RETRIEVER=linkup``.
    """

    # Results are links plus a content excerpt; GPT Researcher scrapes each page as usual.
    requires_scraping = True

    def __init__(
        self,
        query: str,
        headers: dict[str, Any] | None = None,
        query_domains: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Initializes the LinkupSearch object.

        Args:
            query: The search query.
            headers: Request headers. A ``linkup_api_key`` entry takes precedence over the
                ``LINKUP_API_KEY`` environment variable.
            query_domains: Domains to restrict the search to.
            **kwargs: Extra arguments some GPT Researcher call sites pass (ignored).
        """
        self.query = query
        self.headers = headers or {}
        self.query_domains = query_domains or None
        self.api_key = self._retrieve_api_key()
        self.depth = self._retrieve_depth()
        self.client = LinkupClient(api_key=self.api_key)

    def _retrieve_api_key(self) -> str:
        """
        Retrieves the Linkup API key from the headers or environment variables.

        Raises:
            ValueError: If the API key is not found.
        """
        api_key = self.headers.get("linkup_api_key") or os.environ.get("LINKUP_API_KEY")
        if not api_key:
            raise ValueError(
                "Linkup API key not found. Please set the LINKUP_API_KEY environment variable. "
                "You can obtain your key from https://app.linkup.so/"
            )
        return str(api_key)

    def _retrieve_depth(self) -> Depth:
        """Reads the search depth from ``LINKUP_DEPTH``, defaulting to ``standard``."""
        depth = os.environ.get("LINKUP_DEPTH", _DEFAULT_DEPTH).strip().lower()
        if depth not in _DEPTHS:
            logger.warning(
                "Invalid LINKUP_DEPTH %r; expected one of %s. Using %r.",
                depth,
                ", ".join(_DEPTHS),
                _DEFAULT_DEPTH,
            )
            return _DEFAULT_DEPTH
        return cast(Depth, depth)

    def search(self, max_results: int = 10) -> list[dict[str, Any]]:
        """
        Searches the query using the Linkup API.

        Args:
            max_results: The maximum number of results to return.

        Returns:
            A list of ``{"href", "body"}`` dicts, or an empty list if the request fails.
        """
        try:
            response = self.client.search(
                self.query,
                depth=self.depth,
                output_type="searchResults",
                include_domains=self.query_domains,
                max_results=max_results,
            )
        except Exception as e:
            logger.warning("Failed fetching sources from Linkup: %s", e)
            return []

        if not isinstance(response, LinkupSearchResults):
            return []

        search_response: list[dict[str, Any]] = []
        for result in response.results:
            if not isinstance(result, LinkupSearchTextResult) or not result.url:
                continue
            search_response.append({"href": result.url, "body": result.content or ""})
        return search_response[:max_results]

    def answer(self) -> dict[str, Any]:
        """
        Answers the query with a Linkup sourced answer.

        Not used by GPT Researcher's research pipeline; available for direct use.

        Returns:
            A dict with the ``answer`` text and its ``sources`` as ``{"href", "title", "body"}``.
        """
        response = self.client.search(
            self.query,
            depth=self.depth,
            output_type="sourcedAnswer",
            include_domains=self.query_domains,
        )
        if not isinstance(response, LinkupSourcedAnswer):
            raise TypeError(f"Unexpected Linkup response type: {type(response).__name__}")
        return {
            "answer": response.answer,
            "sources": [
                {"href": source.url, "title": source.name, "body": source.snippet or ""}
                for source in response.sources
                if source.url
            ],
        }

    def fetch(self, url: str, render_js: bool = False) -> dict[str, Any]:
        """
        Fetches a web page as markdown using the Linkup API.

        Not used by GPT Researcher's research pipeline; available for direct use.

        Args:
            url: The URL of the page to fetch.
            render_js: Whether to render JavaScript before extracting the content.

        Returns:
            A ``{"href", "raw_content"}`` dict with the page content as markdown.
        """
        response = self.client.fetch(url, render_js=render_js)
        return {"href": url, "raw_content": response.markdown}
