# gptr-linkup-retriever

[![PyPI version](https://badge.fury.io/py/gptr-linkup-retriever.svg)](https://pypi.org/project/gptr-linkup-retriever/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

A [GPT Researcher](https://github.com/assafelovic/gpt-researcher) retriever plugin for the
[Linkup API](https://www.linkup.so). Linkup searches the web in real time and returns relevant,
citable sources, which GPT Researcher then scrapes and uses to write its report.

The package registers the retriever under the `gpt_researcher.retrievers` entry-point group, as
described in GPT Researcher's
[Retriever Plugins](https://docs.gptr.dev/docs/gpt-researcher/search-engines/retriever-plugins)
docs. No change to GPT Researcher is needed.

## Installation

```bash
pip install gptr-linkup-retriever
```

Requires Python 3.12+ and `gpt-researcher>=0.16.1` (the first release that loads retriever plugins).

## Quickstart

Get an API key from the [Linkup app](https://app.linkup.so), then select the retriever:

```bash
export LINKUP_API_KEY=...
export RETRIEVER=linkup
```

```python
import asyncio

from gpt_researcher import GPTResearcher


async def main() -> None:
    researcher = GPTResearcher(query="What changed in the latest Python release?")
    await researcher.conduct_research()
    print(await researcher.write_report())


asyncio.run(main())
```

Linkup can be combined with built-in retrievers, e.g. `RETRIEVER=linkup,duckduckgo`.

## Configuration

| Environment variable | Description                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------------- |
| `LINKUP_API_KEY`     | Your Linkup API key (required).                                                               |
| `LINKUP_DEPTH`       | Search depth: `fast`, `standard` (default) or `deep`. `deep` is slower but better for complex queries. |

The API key can also be passed per request through GPT Researcher's `headers`, as
`{"linkup_api_key": "..."}`, which takes precedence over the environment variable.

When GPT Researcher is given `query_domains`, they are sent to Linkup as `includeDomains`, so
results come only from those domains.

## Direct use

The retriever can also be used on its own. Besides `search`, it exposes `answer` (a sourced answer)
and `fetch` (a web page as markdown); GPT Researcher's pipeline only calls `search`.

```python
from gptr_linkup_retriever import LinkupSearch

retriever = LinkupSearch("What is the latest stable Python version?", query_domains=["python.org"])
results = retriever.search(max_results=5)  # [{"href": ..., "body": ...}, ...]
answer = retriever.answer()  # {"answer": ..., "sources": [{"href", "title", "body"}, ...]}
page = retriever.fetch("https://docs.python.org/3/whatsnew/index.html")  # {"href", "raw_content"}
```

`search` returns an empty list on API errors so that a failing request does not abort a research
run; `answer` and `fetch` raise the Linkup SDK errors.

## Development

```bash
make install-dev
make test
```

## Links

- [Linkup documentation](https://docs.linkup.so)
- [GPT Researcher retriever plugins](https://docs.gptr.dev/docs/gpt-researcher/search-engines/retriever-plugins)
