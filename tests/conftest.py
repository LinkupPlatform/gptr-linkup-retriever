import pytest


@pytest.fixture(autouse=True)
def linkup_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINKUP_API_KEY", "test-api-key")
    monkeypatch.delenv("LINKUP_DEPTH", raising=False)
