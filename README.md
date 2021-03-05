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

There are also some simple classes that can take advantage of the types built-in to Brick / Haystack to build new graphs:
```python
from rdflib import Namespace
import tasty.constants as tc
import tasty.graphs as tg
from tasty.entities import HaystackPointDefs, HaystackEquipDefs, BrickPointDefs, BrickEquipmentDefs

# Create a namespace and load in a blank Brick / Haystack graph
EX = Namespace('example.com#')
hg = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_10)
bg = tg.get_versioned_graph(tc.BRICK, tc.V1_1)

# Wrapper classes around entity types
hp = HaystackPointDefs(tc.V3_9_10)
bp = BrickPointDefs(tc.V1_1)
he = HaystackEquipDefs(tc.V3_9_10)
be = BrickEquipmentDefs(tc.V1_1)

# Bind all of the first class types as attributes
# to the classes
hp.bind()
bp.bind()
he.bind()
be.bind()

# Create a new point from one of the types and view the docs
chw_flow_sensor = hp.chilled_water_flow_sensor.deep_copy()
chw_flow_sensor.type_docs() # 'Sensor which measures the volumetric flow of chilled water'
chw_flow_sensor.type_uri() # 'https://project-haystack.org/def/phIoT/3.9.10#chilled-water-flow-sensor'

# Generate an id for the point and bind it to a namespace
chw_flow_sensor.gen_uuid() # UUID('2733f091-be5b-4983-b701-b7e42c52b72c')
chw_flow_sensor.set_namespace(EX) # True

# Add the entity to the graph hg
chw_flow_sensor.bind_to_graph(hg)
```

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
