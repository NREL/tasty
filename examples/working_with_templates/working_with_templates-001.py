import os

import tasty.templates as tt
import tasty.graphs as tg

# Output directory
output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

# Get a base graph
ont = tg.load_ontology('Haystack', '3.9.9')
point_type_string = 'cur-air-writable-motor-curVal-sensor-point'

# Define expected Datatype properties.
# Properties
fields = {
    'curVal': {
        '_kind': 'number',
        'val': None
    },
    'unit': 'cfm'
}

# Result of the below is a set like: {(Namespace, term), (Namespace, term), ...}
ns_terms = tt.get_namespaced_terms(ont, point_type_string)
ns_fields = tt.get_namespaced_terms(ont, fields)

structured_terms = tt.hget_entity_classes(ont, ns_terms)

# Here we use the ns_fields.
et = tt.EntityTemplate(structured_terms['classes'], structured_terms['markers'], ns_fields)

# To create a grouping of points, we use the concept
# of a PointGroupTemplate.
# We populate the PGT with an empty dictionary
# and then add the above EntityTemplate to it.
# Although this is valid, mainly it's best to
# populate from a valid PGT - see below
pgt = tt.PointGroupTemplate({})
pgt.add_telemetry_point_to_template(et)

# The PointGroupTemplate is not valid:
print(f"PointGroupTemplate valid? {pgt.is_valid}")
