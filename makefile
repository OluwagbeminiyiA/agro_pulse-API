.PHONY: run-server lint all clean test

all:
	lint

clean:
	rmdir \\s .cache .ruff_cache .pytest_cache

test:
	@echo "No tests implemented yet"

run-server:
	poetry run python -m core_agropulse.manage runserver

lint:
	poetry run pre-commit run --all-files
