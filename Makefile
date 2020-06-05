_python_pkg := coronavirus_berlin_scraper

.PHONY: setup
setup:  ## Create Pipenv virtual environment and install dependencies.
	pipenv --three --site-packages
	pipenv install

.PHONY: setup-dev
setup-dev:  ## Install development dependencies
	pipenv install --dev

.PHONY: test
test:  ## Run unit tests
	pipenv run python -m unittest

.PHONY: lint
lint:  ## Run linting
	pipenv run flake8 $(_python_pkg)
	pipenv run mypy $(_python_pkg) --ignore-missing-imports
	pipenv run isort -c -rc $(_python_pkg)

.PHONY: tox
tox:  ## Test with tox
	tox -r

.PHONY: reformat
reformat:  ## Reformat Python code using Black
	black -l 79 --skip-string-normalization $(_python_pkg)
	pipenv run isort -rc $(_python_pkg)

.PHONY: python-shell
python-shell:  ## Run Python shell with all dependencies installed
	pipenv run ipython --no-banner --no-confirm-exit

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'
