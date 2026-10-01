install-dev:
	@echo "Installing local package..."
	uv sync
	uv run prek install
test:
	@echo "Running tests..."
	uv run prek run --all-files
	uv run mypy .
	uv run pytest --cov=src/gptr_linkup_retriever/ --cov-report term-missing --disable-socket --allow-unix-socket tests

update-dependencies:
	uv lock --upgrade
update-pre-commit-hooks:
	uv run prek autoupdate --cooldown-days 14
