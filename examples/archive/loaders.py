# imports and setup

import tasty.templates as tt
import tasty.graphs as tg
import tasty.constants as tc


def initialize_pgt_notebook():
    haystack_ont = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
    brick_ont = tg.load_ontology(tc.BRICK, tc.V1_1)

    point_type_string = 'cur-writable-motor-run-curVal-sensor-point'
    haystack_namespaced_terms = tt.get_namespaced_terms(haystack_ont, point_type_string)

    brick_type = 'Damper_Position_Command'
    brick_namespaced_terms = tt.get_namespaced_terms(brick_ont, brick_type)

    haystack_properties = {
        'curVal': {
            '_kind': 'number',
            'val': None
        },
        'unit': 'cfm'
    }

    namespaced_properties = tt.get_namespaced_terms(haystack_ont, haystack_properties)
    structured_terms = tt.hget_entity_classes(haystack_ont, haystack_namespaced_terms)

    # For Brick, we don't have any additional 'typing properties' or fields, so we initialize those as empty sets
    tt.EntityTemplate(entity_classes=brick_namespaced_terms,
                      schema_name='Brick',
                      schema_version='1.1',
                      typing_properties=set(),
                      properties=set())

    # For Haystack, use namespaced_fields instead of structured_terms['fields']
    tt.EntityTemplate(structured_terms['classes'],
                      'Haystack',
                      '3.9.9',
                      structured_terms['markers'],
                      namespaced_properties)


def initialize_eqt_notebook():
    initialize_pgt_notebook()

    haystack_pgt_dict = {
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
    return haystack_pgt_dict


haystack_eqt_dict = {
    'id': 'b6f175ef-e172-4a02-9aa6-8d930a8222a8',
    'symbol': 'VAV_CO_SD',
    'description': 'Single duct, cooling only VAV',
    'template_type': 'equipment-template',
    'schema_name': 'Haystack',
    'version': '3.9.9',
    'extends': 'coolingOnly-vav',
    'properties': {
        'singleDuct': {'_kind': 'marker'},
        'ratedAirflow': {'_kind': 'number', 'val': 123}
    },
    'telemetry_point_types': {
        'SD': None,
        'damper-cmd-point': {'curVal': {'_kind': 'bool'}}
    }
}

brick_eqt_dict = {
    'id': 'b6b75737-c33b-4c20-88a2-0f9f91271af9',
    'symbol': 'VAV_CO_SD',
    'description': 'Single duct, cooling only VAV',
    'template_type': 'equipment-template',
    'schema_name': 'Brick',
    'version': '1.1',
    'extends': 'Variable_Air_Volume_Box',
    'properties': {},
    'telemetry_point_types': {
        'SD': None,
        'Damper_Position_Command': {}
    }
}
