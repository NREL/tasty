# tasty

Tasty was created to:
1. Get Metadata Schema and Modeling tools into as many projects as possible.
1. Provide a consistent methodology to define templates for "buildings things" (equipment, points, systems, etc.)
1. Provide and SDK for building up Metadata Models using these templates.

# Core Concepts
- We are talking about things in / around / inside / outside / upsidownsides of buildings:
    - Things have classes
    - Things have properties
    - Things have relationships to other things
- We don't need more metadata standards, we need better metadata tooling:
    - One-size fits all validation doesn't work
    - Use-case oriented validation is needed
    - Haystack, Brick, Google Digital Buildings - all do things well
    - Giving people the tools to build things well will inherently provide more consistent implementations.


# Usage and Examples
- See [Usage](examples/README.md)


# Setup
This repository is setup to work with pyenv and poetry:
- [pyenv](https://github.com/pyenv/pyenv#installation) for managing python versions
- [poetry](https://python-poetry.org/docs/#installation) for managing environment
- [pre-commit](https://pre-commit.com/#install) for managing code styling

## Using Poetry
Once poetry is installed:
- `poetry config virtualenvs.in-project true` setting to create a .venv dir in your project and install dependencies there (similar to `.bundle/install`)
- Clone this repo, cd into it
- `pyenv local 3.7.4`
- `poetry install` add `--no-dev` flag if don't want development requirements and `--no-root` if don't want to install the current project
- `poetry run pre-commit install` install git hooks
- `poetry run pre-commit run --all-files` run pre-commit through poetry
- `poetry add [package]` adds package as dependency, specify `--dev` flag if dev dependency
- `poetry shell` enter a virtual environment through poetry

# Tests
- `poetry run pytest`
