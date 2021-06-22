# tasty

Tasty was created to simplify the generation and validation of metadata related to buildings and intends to support the following schemas.

- [Brick](https://brickschema.org/)
- [Project Haystack](https://project-haystack.org/)
- [ASHRAE Standard 223P](https://www.ashrae.org/about/news/2018/ashrae-s-bacnet-committee-project-haystack-and-brick-schema-collaborating-to-provide-unified-data-semantic-modeling-solution)

# Installing

## Prerequisites
- Clone or download the repository.
- Install [Python](https://www.python.org/downloads/) (>=3.3 recommended).
- Install [Poetry](https://python-poetry.org/docs/#installation).

## Steps
1. Create a virtual environment within the repository. The following command will create a virtual environment with [venv](https://docs.python.org/3/library/venv.html) (included with Python >=3.3) named `venv_name`.
   ```bash
   python3 -m venv venv_name
   ```
2. Install dependencies.
   ```bash
   poetry install
   ```
3. Run tasty to confirm that it's working, which should show a message describing its usage.
   ```bash
   poetry run tasty
   ```

# Using

## Generate shapes
The core shape templates (`tasty/source_shapes/*`) are used to generate the SHACL shape files. Run the following to generate the SHACL shape files locally.
```bash
poetry run tasty generate-shapes
```

### OAP shapes
Tasty can scrape the [BuildingsIOT Ontology Alignment Project (OAP)](https://oap.buildingsiot.com/) for all of their points and functions and then use these to create a source shapes file with the following commands.

1. Scrape data to `tasty/utils/temp/`.
   ```bash
   poetry run python tasty/utils/scrape_oap.py
   ```
2. Generate shapes to `tasty/source_shapes/haystack/oap.json`.
   ```bash
   poetry run python tasty/utils/generate_oap.py
   ```

### Run tests
You should now be able to run the tests, make sure they are all passing: 
```bash
poetry run pytest
```

## Generate input file to use for validation
You can use tasty to help you validate instance data against specific shapes. To do this, you must first generate an input file. Each row in an input file corresponds to an entity in your instance data. An input file will contain the following column headers:
- `entity-id`: A namespaced id for entities in a data file you would like to validate.
- `entity-name`: Optionally a description for the entity, helpful for reading.

Additional column headers will exist for each of the shapes you want to use to validate your data. The easiest way to generate an input file is to also merge in data from an existing RDF graph (`-dg` option). Try this with one of the test files (an `input-file.csv` will appear in your root directory):
```bash
poetry run tasty generate-input -dg tests/files/data/haystack_g36_data_3_9_10.ttl
```
- Add the `-c` flag to only add composite shapes to your input file. Composite meaning shapes having other shape, i.e. a shape for a specific vav box configuration, etc.

## Validate instance data
Using the generated `input-file.csv`, mark an `X` in the cells according to the shape you want the entity to validate against. Using the example generated from above, the following should be true:

| Entity | phShapes:G36-Base-VAV-Shape | phShapes:G36-CoolingOnly-VAV-Shape | phShapes:G36-HotWaterReheat-VAV-Shape | phShapes:HotWaterReheatFdbk-VAV-Shape |
| --- | --- | --- | --- | --- |
| VAV-01 | Valid | Valid | Invalid | Invalid | Invalid |
| VAV-02 | Valid | Valid | Valid | Valid | Invalid |
| VAV-03 | Valid | Valid | Valid | Valid | Valid |

Save the file. Each entity can now be validated against the indicated shape. To validate the file, simply run:
```bash
poetry run tasty validate -dg tests/files/data/haystack_g36_data_3_9_10.ttl
```

Outputs will be printed to the terminal, but you can also find a validation report as a ttl file in your root. Should look something like `results-haystack_g36_data_3_9_10.ttl`.

## Python
There are also some simple classes that can take advantage of the types built-in to Brick / Haystack.
```python
from rdflib import Namespace
import tasty.constants as tc
import tasty.graphs as tg
from tasty.entities import HaystackPointDefs, HaystackEquipDefs, BrickPointDefs, BrickEquipmentDefs

# Create a namespace and load in a blank Brick / Haystack graph
EX = Namespace('example.com#')
hg = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_10)
bg = tg.get_versioned_graph(tc.BRICK, tc.V1_1)

# Specify the schema version (tc.V9_9_10, etc.) to use
hp = HaystackPointDefs(tc.V3_9_10)
bp = BrickPointDefs(tc.V1_1)
he = HaystackEquipDefs(tc.V3_9_10)
be = BrickEquipmentDefs(tc.V1_1)

# Bind all of the first class types as attributes
hp.bind()
bp.bind()
he.bind()
be.bind()

# Create a new point from one of the types and view the docs
chw_flow_sensor = hp.chilled_water_flow_sensor.deep_copy()
chw_flow_sensor.type_docs() # 'Sensor which measures the volumetric flow of chilled water'
chw_flow_sensor.type_uri() # 'https://project-haystack.org/def/phIoT/3.9.10#chilled-water-flow-sensor'

# Generate an id for the point and bind it to a namespace
chw_flow_sensor.set_id() # UUID('2733f091-be5b-4983-b701-b7e42c52b72c')
chw_flow_sensor.set_namespace(EX) # True

# Add the entity to the graph hg
chw_flow_sensor.bind_to_graph(hg)
```

## Examples
Jupyter Lab is currently a dev dependency. If you have gone through the poetry setup, run:
- `poetry run jupyter lab`
- Open the [NREL VAV Cooling Only.ipynb](./examples/NREL%20VAV%20Cooling%20Only.ipynb)

# Developing
Recommended setup documented [here](https://gist.github.com/corymosiman12/26fb682df2d36b5c9155f344eccbe404)
