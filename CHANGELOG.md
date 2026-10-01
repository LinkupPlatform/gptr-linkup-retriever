# CHANGELOG

<!-- version list -->

## v0.1.0 (2026-10-01)

### Features

- Initial release: `LinkupSearch` retriever for GPT Researcher, registered as `RETRIEVER=linkup`
  through the `gpt_researcher.retrievers` entry-point group, with `query_domains` support, a
  configurable search depth (`LINKUP_DEPTH`), and `answer` / `fetch` helpers for direct use.
