.PHONY: minimal
minimal: setup

.PHONY: setup
setup:
	uv sync
	uv run pre-commit install --install-hooks

.PHONY: test
test:
	uv run coverage erase
	uv run coverage run -m pytest --strict-markers tests
	uv run coverage report --show-missing --include=tests/* --fail-under 99
	uv run coverage report --show-missing --include=testing/* --fail-under 100
	uv run coverage report --show-missing --skip-covered --include=detect_secrets/* --fail-under 95
	uv run ty check
	uv run pre-commit run --all-files

.PHONY: format
format:
	uv run ruff check --fix .
	uv run ruff format .

.PHONY: clean
clean:
	find -name '*.pyc' -delete
	find -name '__pycache__' -delete

.PHONY: super-clean
super-clean: clean
	rm -rf .venv
	rm -rf .ruff_cache
