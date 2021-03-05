import os
import uuid
import csv

import pytest

import tasty.templates as tt
import tasty.graphs as tg
import tasty.constants as tc
from tasty.generated import generated_dir


def populate_point_group_template_from_file(file_path):
    # -- Setup
    templates = tt.load_template_file(file_path)
    assert len(templates) == 1

    template_data = templates[0]
    pgt = tt.PointGroupTemplate(**template_data)
    pgt.populate_template_basics()
    pgt.resolve_telemetry_point_types()

    return template_data, pgt


def populate_equipment_template_from_file(file_path):
    templates = tt.load_template_file(file_path)
    assert len(templates) == 1

    template_data = templates[0]
    eq = tt.EquipmentTemplate(**template_data)
    assert eq.is_valid

    # -- Setup - populate basics
    eq.populate_template_basics()
    eq.resolve_extends()

    return eq


def prep_for_write(output_dir, file, write_type, ext):
    file_name = os.path.splitext(os.path.basename(file))[0]
    out_file = os.path.join(output_dir, f"{write_type}-{file_name}.{ext}")
    if os.path.isfile(out_file):
        os.remove(out_file)
    return out_file


def reset_base_template_instance_ids():
    # NEVER DO THIS IN PRACTICE
    tt.BaseTemplate._instance_ids = set()
    assert len(tt.BaseTemplate._instance_ids) == 0


def reset_point_group_template_registration():
    # NEVER DO THIS IN PRACTICE
    tt.PointGroupTemplate.instances = set()
    assert len(tt.PointGroupTemplate.instances) == 0


@pytest.fixture
def minimum_entity_template():
    classes = set([(tc.BRICK_1_1, 'Damper_Position_Command')])
    et = tt.EntityTemplate(classes, tc.BRICK, tc.V1_1, set(), set())
    return et


@pytest.fixture
def haystack_entity_template():
    # -- Setup
    schema_name = 'Haystack'
    schema_version = '3.9.9'
    ont = tg.load_ontology(schema_name, schema_version)
    point_type_string = 'cur-his-discharge-air-temp-sensor-point'
    properties = {
        'curVal': {
            '_kind': 'number',
            'val': None
        },
        'unit': 'cfm'
    }
    # -- Act
    ns_terms = tt.get_namespaced_terms(ont, point_type_string)
    ns_properties = tt.get_namespaced_terms(ont, properties)
    structured_terms = tt.hget_entity_classes(ont, ns_terms)

    et = tt.EntityTemplate(structured_terms['classes'], schema_name, schema_version, structured_terms['markers'],
                           ns_properties)
    return et


@pytest.fixture
def brick_entity_template():
    # -- Setup
    schema_name = 'Brick'
    schema_version = '1.1'
    ont = tg.load_ontology(schema_name, schema_version)
    point_type_string = 'Discharge_Air_Flow_Sensor'
    ns_terms = tt.get_namespaced_terms(ont, point_type_string)

    et = tt.EntityTemplate(ns_terms, schema_name, schema_version, set(), set())
    return et


@pytest.fixture
def bad_ids():
    return [1, 'sdf', {}, []]


@pytest.fixture
def bad_uuids():
    return [
        ('d72ef4fe-3a4d-11eb-8926-3af9d38d2919', 1),
    ]


@pytest.fixture
def my_uuid4():
    return '794a4888-162b-468d-bb39-2afbe90ecd34'


@pytest.fixture
def equipment_template_bad_template_type():
    t = {
        'id': str(uuid.uuid4()),
        'symbol': 'ABCDE',
        'template_type': 'point-group-template',
        'schema_name': 'Haystack',
        'version': '3.9.9'
    }
    return t


@pytest.fixture
def point_group_template_bad_template_type():
    t = {
        'id': str(uuid.uuid4()),
        'symbol': 'ABCDE',
        'template_type': 'equipment-template',
        'schema_name': 'Haystack',
        'version': '3.9.9'
    }
    return t


@pytest.fixture
def get_occupancy_mode_data():
    g = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_9)
    f = os.path.join(os.path.dirname(__file__), 'files/data/occupancy_mode_data.ttl')
    g.parse(f, format='turtle')
    return g


@pytest.fixture
def get_occupancy_mode_shapes():
    g = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_9)
    f = os.path.join(os.path.dirname(__file__), 'files/shapes/occupancy_mode_shapes.ttl')
    g.parse(f, format='turtle')
    return g


@pytest.fixture
def get_g36_data():
    g = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_9)
    f = os.path.join(os.path.dirname(__file__), 'files/data/g36_data.ttl')
    g.parse(f, format='turtle')
    return g


@pytest.fixture
def get_g36_data2():
    g = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_10)
    f = os.path.join(os.path.dirname(__file__), 'files/data/g36_data_3_9_10.ttl')
    g.parse(f, format='turtle')
    return g


@pytest.fixture
def get_g36_shapes():
    g = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_9)
    f = os.path.join(os.path.dirname(__file__), 'files/shapes/g36_shapes.ttl')
    g.parse(f, format='turtle')
    return g


@pytest.fixture
def get_core_shapes2():
    g = tg.get_versioned_graph(tc.HAYSTACK, tc.V3_9_10)
    f = os.path.join(generated_dir, 'core_v2.ttl')
    g.parse(f, format='turtle')
    return g


def get_single_node_validation_query():
    # -- This query returns us three values that looks like:
    #    (focus_node, path, missing_value)
    q = ''' SELECT ?focus ?path ?val WHERE {
        ?vr a sh:ValidationReport .
        ?vr sh:result ?r .
        ?r sh:focusNode ?focus .
        ?r sh:resultPath ?path .
        ?r sh:sourceShape ?shape .
        ?shape sh:qualifiedValueShape ?vs .
        ?vs sh:hasValue ?val .
        }
    '''
    return q


def get_parent_node_validation_query():
    # -- This query returns us a triple that looks like:
    #   (focus_node, inverse_path, constraint_triggered, shape)
    q = ''' SELECT ?focus ?inverse_path ?constraint ?shape WHERE {
        ?vr a sh:ValidationReport .
        ?vr sh:result ?r .
        ?r sh:focusNode ?focus .
        ?r sh:resultPath ?path .
        ?path sh:inversePath ?inverse_path .
        ?r sh:sourceConstraintComponent ?constraint .
        ?r sh:sourceShape ?source_shape .
        ?source_shape sh:qualifiedValueShape ?shape .
        }
    '''
    return q


def get_min_count_validation_query():
    # -- This query returns us a triple that looks like:
    #   (focus_node, inverse_path, constraint_triggered, shape)
    q = ''' SELECT ?focus ?inverse_path ?constraint ?message WHERE {
        ?vr a sh:ValidationReport .
        ?vr sh:result ?r .
        ?r sh:focusNode ?focus .
        ?r sh:resultPath ?path .
        ?path sh:inversePath ?inverse_path .
        ?r sh:sourceConstraintComponent ?constraint .
        ?r sh:resultMessage ?message .
        }
    '''
    return q


def get_severity_query():
    q = ''' SELECT ?focus ?severity WHERE {
        ?vr a sh:ValidationReport .
        ?vr sh:result ?r .
        ?r sh:focusNode ?focus .
        ?r sh:resultSeverity ?severity .
        }
    '''
    return q


def assert_remove_markers(remove_markers, results_query, point, ont_graph=tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)):
    print(f"Remove: {remove_markers}")
    namespaced_terms = []
    for marker in remove_markers:
        ns_term = tg.get_namespaced_term(ont_graph, marker)
        if ns_term:
            namespaced_terms.append(ns_term)
    for row in results_query:
        print(row)
        assert len(results_query) == len(remove_markers)
        for marker in remove_markers:
            # subject should always be the point
            assert row[0] == point
            # predicate should always be hasTag
            assert row[1] == tc.PH_DEFAULT.hasTag
            # object should be the removed marker
            assert row[2] in namespaced_terms


def write_csv(results_query, output_file):
    with open(output_file.replace('.ttl', '.csv'), 'w+') as f:
        writer = csv.writer(f)
        for row in results_query:
            writer.writerow(row)
