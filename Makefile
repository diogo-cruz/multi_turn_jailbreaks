.PHONY: format

format:
	ruff check --fix .
	ruff format .
