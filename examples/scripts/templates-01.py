import os

import tasty.templates as tt
import tasty.constants as tc
import tasty.graphs as tg


output_dir = os.path.join(os.path.dirname(__file__), 'outputs')
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

# Get a base graph
ont = tg.load_ontology('Haystack', '3.9.9')
point_type_string = 'cur-air-writable-motor-curVal-sensor-point'

# Define expected Datatype properties.
fields = {
    'curVal': {
        '_kind': 'number',
        'val': None
    },
    'unit': 'cfm'
}

# Resolve content to namespaced terms based on the loaded ontology.
# Result of the below is a set like: {(Namespace, term), (Namespace, term), ...}
ns_terms = tt.get_namespaced_terms(ont, point_type_string)
ns_fields = tt.get_namespaced_terms(ont, fields)

structured_terms = tt.hget_entity_classes(ont, ns_terms)

# Here we use the ns_fields.
et = tt.EntityTemplate(structured_terms['classes'], structured_terms['markers'], ns_fields)


# In the following, we populate the PGT with an empty dictionary
# and then add the above EntityTemplate to it.
# Although this is valid, mainly it's best to
# populate from a valid PGT - see below
pgt = tt.PointGroupTemplate({})
pgt.add_telemetry_point_to_template(et)

# The PointGroupTemplate is not valid:
print(f"pgt valid? {pgt.is_valid}")


# A PointGroupTemplate is instantiated from a dictionary with
# the proper keys.  It looks as follows (this is a similar Python dict representation
# of the tests/files/haystack-point-group-template-1.yaml, slightly modified)

pgt_dict = {
    'id': '4aa753fc-ab1b-47d0-984f-121fa0cfa0e9',
    'symbol': 'SD',
    'description': 'Single duct VAV type, with basic airflow control.',
    'template_type': 'point-group-template',
    'schema_name': 'Haystack',
    'version': '3.9.9',
    'telemetry_point_types': {
        'discharge-air-flow-sensor-point-cur-his': {
            'curVal': {
                '_kind': 'number',
                'val': None
            },
            'unit': {
                '_kind': 'str',
                'val': 'cfm'
            }
        },
        'discharge-air-flow-sp-point': {},
        'damper-cmd-point': {
            'unit': 'percent'
        }
    }
}

# since the dict is not empty, this will automatically attempt
# to validate the template against the template schema
pgt_valid = tt.PointGroupTemplate(pgt_dict)

print(f"pgt valid? {pgt_valid.is_valid}")

# Although it's valid, we still need to populate:
# 1. the template basics
# 2. the telemetry points
pgt_valid.populate_template_basics()
pgt_valid.resolve_telemetry_point_types()
# For each point type (i.e. key in 'telemetry_point_types'),
# an Entity Template is created and registered within the class.

###
# Section 5 - Explore EntityTemplates and PointGroupTemplates
###
# We can now do a few cool things:

# We can find Entity Templates of a certain class.
to_find = (tc.PHIOT_3_9_9, 'cur-point')
et_of_interest = tt.EntityTemplate.find_with_class(to_find)

# This should return two EntityTemplates:
# 1. ET created in Section 2
# 2. ET created as part of the PointGroupTemplate population in Section 4
print(f"There are {len(et_of_interest)} EntityTemplates based on the {to_find} class")

# Or even of multiple classes:
to_find = set([(tc.PHIOT_3_9_9, 'cur-point'), (tc.PHIOT_3_9_9, 'his-point')])
et_of_interest = tt.EntityTemplate.find_with_classes(to_find)
# This should return only 1 EntityTemplate:
# ET created as part of the PointGroupTemplate population in Section 4.
# The ET created in Section 1 has clases of cur-point and writable-point


print(f"There are {len(et_of_interest)} EntityTemplates based on the {to_find} classes")

# 2. We can find all Point Group Templates that have those entities of interest:
for et in et_of_interest:
    for pgt in tt.PointGroupTemplate.all_templates:
        if et in pgt.telemetry_point_entities:
            print(f"EntityTemplate with typing info: {et.get_simple_typing_info()} found in PGT: {pgt._id}")
