# tasty

Provides an SDK for building up semantic metadata models using a templating framework.

There are three valid template types enabled by tasty:
- `point-group-template`: very similar to the [ABSTRACT.yaml](https://github.com/google/digitalbuildings/blob/master/ontology/yaml/resources/HVAC/entity_types/ABSTRACT.yaml) used in the GDB project
- `entity-template`:
- `system-template`:

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


## Working with tasty graphs
```python
import tasty.graphs as tg

# Load an ontology into a new rdflib Graph
brick_ont = tg.load_ontology(schema='Brick', version='1.1')
haystack_ont = tg.load_ontology(schema='Haystack', version='3.9.9')

# Get the namespace for a term
ns = tg.get_namespaces_given_term(ontology=brick_ont, term='Discharge_Air')
# returns: [Namespace('https://brickschema.org/schema/1.1/Brick#')]
ns = tg.get_namespaces_given_term
```

## Working with tasty templates
```python
import os
import tasty.constants as tc
import tasty.templates as tt

# Load in template from file, validate against the template schema
template_file = './tests/files/point-group-template-1.yaml'
schema_file = os.path.join(tc.SCHEMAS_DIR, 'template.schema.json')
template = tt.load_template_file(template_file)
template_schema = tt.load_template_schema(schema_file)

is_valid, err = tt.validate_template_against_schema(instance=template[0], schema=template_schema)

# Define telemetry points with additional metadata and create new EntityTemplates for each point type defined
telemetry_point_types = {
    "damper-cmd-point": {
        "kind": "Number",
        "unit": "percent"
    },
    "discharge-air-flow-sensor-point": {
        "curVal": None,
        "kind": "Number",
        "unit": "cfm"
    },
    "discharge-air-flow-sp-point": {
        "kind": "Number",
        "unit": "cfm"
    }
}

entity_templates = tt.resolve_telemetry_points_to_entity_templates(telemetry_point_types, 'Haystack', '3.9.9')
```
