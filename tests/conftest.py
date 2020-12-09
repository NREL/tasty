import os

import pytest
import tasty.templates as tt
import tasty.graphs as tg


def populate_point_group_template_from_file(file_path):
    # -- Setup
    templates = tt.load_template_file(file_path)
    assert len(templates) == 1

    template_data = templates[0]
    pgt = tt.PointGroupTemplate(template_data)
    pgt.populate_template_basics()
    pgt.resolve_telemetry_point_types()

    return template_data, pgt


def populate_equipment_template_from_file(file_path):
    templates = tt.load_template_file(file_path)
    assert len(templates) == 1

    template_data = templates[0]
    eq = tt.EquipmentTemplate(template_data)
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


def reset_point_group_template_registration():
    tt.PointGroupTemplate.instances = set()
    assert len(tt.PointGroupTemplate.instances) == 0


def reset_entity_template_registration():
    tt.EntityTemplate.instances = set()
    assert len(tt.EntityTemplate.instances) == 0


@pytest.fixture
def haystack_entity_template():
    # -- Setup
    schema_name = 'Haystack'
    schema_version = '3.9.9'
    ont = tg.load_ontology(schema_name, schema_version)
    point_type_string = 'cur-his-discharge-air-temp-sensor-point'
    fields = {
        'curVal': {
            '_kind': 'number',
            'val': None
        },
        'unit': 'cfm'
    }
    # -- Act
    ns_terms = tt.get_namespaced_terms(ont, point_type_string)
    ns_fields = tt.get_namespaced_terms(ont, fields)
    structured_terms = tt.hget_entity_classes(ont, ns_terms)

    et = tt.EntityTemplate(structured_terms['classes'],
                           structured_terms['markers'],
                           ns_fields,
                           schema_name,
                           schema_version)
    return et


@pytest.fixture
def brick_entity_template():
    # -- Setup
    schema_name = 'Brick'
    schema_version = '1.1'
    ont = tg.load_ontology(schema_name, schema_version)
    point_type_string = 'Discharge_Air_Flow_Sensor'
    ns_terms = tt.get_namespaced_terms(ont, point_type_string)

    et = tt.EntityTemplate(ns_terms, set(), set(), schema_name, schema_version)
    return et
