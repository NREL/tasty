# tasty

Tasty was created to:
1. Get Metadata Schema and Modeling tools into as many projects as possible.
1. Provide a consistent methodology for:
    1. Building metadata models
    1. Validating metadat models
1. Provide an SDK to accomplish the above

# Getting started
1. Build the core shapes: `poetry run python tasty/generate_shapes.py`
1. Create a csv file to input your data: `poetry run python tasty/generate_input_file.py`
    1. Optionally merge in ids from an existing file: `poetry run python tasty/generate_input_file.py path/to/haystack-data.rdf` (support RDF only at this point)
1. For each entity, mark an `X` corresponding to the shape you want the entity to validate against. Save the file.
1. Validate the file: `poetry run python tasty/validate.py path/to/haystack-data.rdf`


# Usage and Examples
- TODO

# Setup
This repository is setup to work with pyenv and poetry:
- [pyenv](https://github.com/pyenv/pyenv#installation) for managing python versions
- [poetry](https://python-poetry.org/docs/#installation) for managing environment
- [pre-commit](https://pre-commit.com/#install) for managing code styling

## Using Poetry
See [here](https://gist.github.com/corymosiman12/26fb682df2d36b5c9155f344eccbe404) for poetry setup info

# Tests
- `poetry run pytest`
