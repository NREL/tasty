import os

import pytest
from unittest import TestCase
from rdflib.namespace import Namespace
from frozendict import frozendict

import tasty.templates as tt
import tasty.constants as tc
import tasty.graphs as tg
import tasty.exceptions as te
from tests.conftest import populate_point_group_template_from_file, populate_equipment_template_from_file, \
    prep_for_write, reset_base_template_instance_ids, reset_point_group_template_registration


FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'output')
HAYSTACK_PGT_FILE_01 = os.path.join(FILES_DIR, 'haystack-point-group-template-1.yaml')
BRICK_PGT_FILE_01 = os.path.join(FILES_DIR, 'brick-point-group-template-1.yaml')
HAYSTACK_EQ_FILE_01 = os.path.join(FILES_DIR, 'haystack-equipment-template-1.yaml')
BRICK_EQ_FILE_01 = os.path.join(FILES_DIR, 'brick-equipment-template-1.yaml')
SCHEMA_FILE_PATH = os.path.join(tc.SCHEMAS_DIR, 'template.schema.json')

if not os.path.isdir(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


class TestTemplateFunctions:
    """
    For testing all the functions in templates.py not part of a class
    """

    @pytest.mark.parametrize('file', [
        HAYSTACK_PGT_FILE_01,
        BRICK_PGT_FILE_01
    ])
    def test_load_template_file_structure(self, file):
        # -- Setup
        assert os.path.isfile(file)

        templates = tt.load_template_file(file)

        # -- Assert
        assert len(templates) == 1
        template = templates[0]
        assert isinstance(template, dict)
        assert isinstance(template['telemetry_point_types'], dict)
        for k, v in template['telemetry_point_types'].items():
            # Objects (dicts) with a key but no value defined
            assert isinstance(v, dict)

    @pytest.mark.parametrize('file', [
        HAYSTACK_PGT_FILE_01,
        BRICK_PGT_FILE_01
    ])
    def test_exemplary_file_is_valid(self, file):
        # -- Setup
        template = tt.load_template_file(file)
        schema = tt.load_template_schema(SCHEMA_FILE_PATH)
        template = template[0]

        # -- Assert
        is_valid, _ = tt.validate_template_against_schema(template, schema)
        if not is_valid:
            print(f"Error: {_}")
        assert is_valid

    @pytest.mark.parametrize("key,error_message", [
        ("id", "'id' is a required property"),
        ("symbol", "'symbol' is a required property"),
        ("template_type", "'template_type' is a required property"),
    ])
    def test_file_is_not_valid_if_keys_missing(self, key, error_message):
        # -- Setup
        template = tt.load_template_file(HAYSTACK_PGT_FILE_01)
        schema = tt.load_template_schema(SCHEMA_FILE_PATH)
        template = template[0]

        # -- Act
        del template[key]

        # -- Assert
        is_valid, err = tt.validate_template_against_schema(template, schema)
        assert not is_valid
        assert err == error_message

    @pytest.mark.parametrize("key,value,error", [
        ("schema_name", "BAD", "'BAD' is not one of ['Brick', 'Haystack']"),
        ("version", "1234", "'1234' is not one of ['1.1', '3.9.9']"),
    ])
    def test_file_is_not_valid_if_keys_have_wrong_values(self, key, value, error):
        # -- Setup
        template = tt.load_template_file(HAYSTACK_PGT_FILE_01)
        schema = tt.load_template_schema(SCHEMA_FILE_PATH)
        template = template[0]

        # -- Act
        template[key] = value

        # -- Assert
        is_valid, err = tt.validate_template_against_schema(template, schema)
        assert not is_valid
        assert err == error


class TestGetNamespacedTerms(TestCase):
    def test_resolves_typical_haystack_tagset(self):
        # -- Setup
        ont = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
        entity_type = 'discharge-air-flow-sensor-point'

        # -- Act
        tags = tt.get_namespaced_terms(ont, entity_type)

        # -- Assert
        assert len(tags) == 5
        assert isinstance(tags, set)

        tags_list = list(tags)
        assert isinstance(tags_list[0], tuple)
        assert isinstance(tags_list[0][0], Namespace)
        assert isinstance(tags_list[0][1], str)

    def test_ignores_duplicate_term_in_haystack_tagset(self):
        # -- Setup
        ont = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
        entity_type = 'discharge-air-discharge-flow-sensor-point'

        # -- Act
        tags = tt.get_namespaced_terms(ont, entity_type)

        # -- Assert
        assert len(tags) == 5

    def test_resolves_brick_class(self):
        # -- Setup
        ont = tg.load_ontology(tc.BRICK, tc.V1_1)
        entity_type = 'Discharge_Air_Flow_Sensor'

        # -- Act
        tags = tt.get_namespaced_terms(ont, entity_type)
        tags_list = list(tags)

        # -- Assert
        assert len(tags) == 1

        assert tags_list[0][0] == tc.BRICK_1_1
        assert tags_list[0][1] == entity_type

    def test_errors_when_term_not_found(self):
        # -- Setup
        ont = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
        entity_type = 'this-sensor'

        # -- Act
        with self.assertRaises(te.TermNotFoundError) as context:
            tt.get_namespaced_terms(ont, entity_type)

        # -- Assert
        assert str(context.exception) == "Candidate 'this' not found in any namespaces in the provided ontology"

    def test_errors_when_term_found_in_multiple_namespaces(self):
        # -- Setup
        ont = tg.load_ontology(tc.BRICK, tc.V1_1)
        entity_type = 'Discharge-Temperature'

        # -- Act
        with self.assertRaises(te.MultipleTermsFoundError) as context:
            tt.get_namespaced_terms(ont, entity_type)
        ex = "Candidate 'Temperature' found in multiple namespaces: [rdflib.term.URIRef(" \
             "'https://brickschema.org/schema/1.1/Brick#'), rdflib.term.URIRef(" \
             "'https://brickschema.org/schema/1.1/BrickTag#')]"

        # -- Assert
        assert str(context.exception) == ex


class TestHGetEntityClasses:
    @pytest.mark.parametrize("tagset, classes, markers, properties", [
        (
            'cur-air-writable-motor-temp-sensor-point', {
                (tc.PHIOT_3_9_9, 'cur-point'),
                (tc.PHIOT_3_9_9, 'motor'),
                (tc.PHIOT_3_9_9, 'writable-point')
            }, {
                (tc.PHSCIENCE_3_9_9, 'air'),
                (tc.PHSCIENCE_3_9_9, 'temp'),
                (tc.PHIOT_3_9_9, 'sensor')
            },
            set()
        ),
        (
            'fan-air-writable-motor-sensor-curVal-point', {
                (tc.PHIOT_3_9_9, 'fan-motor'),
                (tc.PHIOT_3_9_9, 'writable-point')
            }, {
                (tc.PHSCIENCE_3_9_9, 'air'),
                (tc.PHIOT_3_9_9, 'sensor'),
            }, {
                (tc.PHIOT_3_9_9, 'curVal', frozendict({'val': None})),
            }
        ),
        (
            'fan-air-writable-cur-sensor-curVal-point', {
                (tc.PHIOT_3_9_9, 'writable-point'),
                (tc.PHIOT_3_9_9, 'cur-point')
            }, {
                (tc.PHSCIENCE_3_9_9, 'air'),
                (tc.PHIOT_3_9_9, 'sensor'),
                (tc.PHIOT_3_9_9, 'fan')
            }, {
                (tc.PHIOT_3_9_9, 'curVal', frozendict({'val': None})),
            }
        )
    ])
    def test_resolves_as_expected(self, tagset, classes, markers, properties):
        ont = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
        valid_namespaced_terms = tt.get_namespaced_terms(ont, tagset)
        structured = tt.hget_entity_classes(ont, set(valid_namespaced_terms))
        assert list(structured.keys()) == ['classes', 'markers', 'properties']
        assert structured['classes'] == classes
        assert structured['markers'] == markers
        assert structured['properties'] == properties


class TestEntityTemplate:
    @pytest.mark.parametrize('classes, schema_name, version, error', [
        (set(), '', '', "entity_classes must be a set and have atleast one item."),
        (set([True]), '', '', 'each element in entity_classes must be a Tuple'),
        (set([('asdf', 'asdf')]), '', '', 'each element in entity_classes must contain a (Namespace, str) tuple'),
        (set([(tc.BRICK_1_1, True)]), '', '', 'each element in entity_classes must contain a (Namespace, str) tuple'),
        (set([(tc.BRICK_1_1, 'string')]), True, '', 'schema_name must be a string'),
        (set([(tc.BRICK_1_1, 'string')]), '', '', 'schema_name must be non-empty'),
        (set([(tc.BRICK_1_1, 'string')]), 'schema-name', True, 'schema_version must be a string'),
        (set([(tc.BRICK_1_1, 'string')]), 'schema-name', '', 'schema_version must be non-empty'),
    ])
    def test_bad_templates_throw_errors(self, classes, schema_name, version, error):
        try:
            tt.EntityTemplate(classes, schema_name, version, set(), set())

            # should not get here
            assert False
        except ValueError as e:
            assert str(e) == error
        assert len(tt.EntityTemplate.instances) == 0

    def test_minimum_template_is_valid_and_in_instances(self, minimum_entity_template):
        # -- Setup
        et = minimum_entity_template
        assert et.is_valid
        assert et in tt.EntityTemplate.instances  # checks the template was registered

    def test_minimum_template_methods_dont_fail(self, minimum_entity_template):
        # -- Setup expectations
        simple_classes = set(['Damper_Position_Command'])

        et = minimum_entity_template
        assert et.get_simple_classes() == simple_classes
        assert et.get_simple_typing_info() == simple_classes
        assert et.get_simple_properties() == {}
        assert et.get_namespaces() == set([tc.BRICK_1_1])

    def test_initialize_equivalent_returns_original(self, minimum_entity_template):
        et1 = minimum_entity_template
        et2 = minimum_entity_template
        assert et1 is et2

    def test_initialize_similar_does_not_return_original(self):
        classes = set([(tc.BRICK_1_1, 'Damper_Position_Command')])
        schema_name = 'Haystack'
        schema_version = '3.9.9'
        ont = tg.load_ontology(schema_name, schema_version)
        properties1 = {
            'curVal': {
                '_kind': 'number',
                'val': None
            }
        }
        properties2 = {
            'curVal': {
                '_kind': 'number',
                'val': 1
            }
        }
        ns_properties1 = tt.get_namespaced_terms(ont, properties1)
        ns_properties2 = tt.get_namespaced_terms(ont, properties2)
        et1 = tt.EntityTemplate(classes, schema_name, schema_version, set(), ns_properties1)
        et2 = tt.EntityTemplate(classes, schema_name, schema_version, set(), ns_properties2)
        assert et1 is not et2

    def test_create_new_haystack_entity_template(self, haystack_entity_template):
        # -- Setup - define expectations
        simple_classes = {'his-point', 'cur-point'}
        simple_typing_info = {'discharge', 'air', 'temp', 'sensor', 'his-point', 'cur-point'}
        simple_properties = {'curVal': {'_kind': 'number', 'val': None}, 'unit': {'val': 'cfm'}}
        all_ns = {
            tc.PH_3_9_9,
            tc.PHIOT_3_9_9,
            tc.PHSCIENCE_3_9_9
        }

        et = haystack_entity_template
        assert et.get_simple_classes() == simple_classes
        assert et.get_simple_typing_info() == simple_typing_info
        assert et.get_simple_properties() == simple_properties
        assert et.get_namespaces() == all_ns
        assert et in tt.EntityTemplate.instances  # checks the template was registered

    def test_create_new_brick_entity_template(self, brick_entity_template):
        # -- Setup - define expectations
        point_type_string = 'Discharge_Air_Flow_Sensor'
        simple_classes = {point_type_string}
        simple_typing_info = {point_type_string}
        simple_properties = {}
        all_ns = {
            tc.BRICK_1_1
        }

        et = brick_entity_template
        assert et.get_simple_classes() == simple_classes  # Only a single class
        assert et.get_simple_typing_info() == simple_typing_info  # Additional typing info not relevant for Brick at this time
        assert et.get_simple_properties() == simple_properties  # No DataTypeProperties available in Brick as of 1.1
        assert et.get_namespaces() == all_ns
        assert et in tt.EntityTemplate.instances  # checks the template was registered

    @pytest.mark.parametrize('class_to_find, expected_number_templates', [
        ((tc.PHIOT_3_9_9, 'cur-point'), 1),
        ((tc.PHIOT_3_9_9, 'equip'), 0)
    ])
    def test_find_with_class(self, class_to_find, expected_number_templates):
        # -- Setup
        tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
        found = tt.EntityTemplate.find_with_class(class_to_find)

        # -- Assert
        assert len(found) == expected_number_templates


class TestResolveTelemetryPointsToEntityTemplates:

    @pytest.mark.parametrize('file, expected_number_entity_templates', [
        (HAYSTACK_PGT_FILE_01, 3),
        (BRICK_PGT_FILE_01, 3)
    ])
    def test_valid_telemetry_points(self, file, expected_number_entity_templates):
        # -- Setup
        template = tt.load_template_file(file)
        template = template[0]
        tel = "telemetry_point_types"
        assert tel in template.keys()

        # -- Act
        points = template[tel]
        assert isinstance(points, dict)
        schema_name = template['schema_name']
        version = template['version']
        entity_templates = tt.resolve_telemetry_points_to_entity_templates(points, schema_name, version)

        assert isinstance(entity_templates, set)
        for et in entity_templates:
            assert isinstance(et, tt.EntityTemplate)
        assert len(entity_templates) == expected_number_entity_templates


class TestBaseTemplate:
    def test_empty_initialization_throws_error(self):
        try:
            tt.BaseTemplate()
        except te.TastyError as e:
            # -- Assert
            assert str(e) == "tasty.templates.BaseTemplate must have an ID"

    def test_template_id_must_be_uuid(self, bad_ids):
        for id in bad_ids:
            template = {'id': id}
            try:
                tt.BaseTemplate(**template)
            except ValueError as e:
                assert str(e) == f"badly formed hexadecimal UUID string"

    def test_template_id_must_be_uuid4(self, bad_uuids):
        for id in bad_uuids:
            template = {'id': id[0]}
            try:
                tt.BaseTemplate(**template)
            except te.TastyError as e:
                assert str(e) == f"tasty.templates.BaseTemplate ID must be valid UUID4, got: {id[0]} - version: {id[1]}"

    def test_template_with_same_ids_throws_error(self, my_uuid4):
        template = {'id': my_uuid4}

        # Should not throw error
        tt.BaseTemplate(**template)

        # Should throw error
        try:
            tt.BaseTemplate(**template)
        except te.TastyError as e:
            assert str(e) == f"tasty.templates.BaseTemplate with ID: {my_uuid4} already exists."


class TestPointGroupTemplate:
    def test_bad_template_type_throws_template_validation_error(self, point_group_template_bad_template_type):
        try:
            tt.PointGroupTemplate(**point_group_template_bad_template_type)

            # Should not reach here
            assert False is True
        except te.TemplateValidationError as e:
            assert str(e) == 'template_type must be: point-group-template'

    @pytest.mark.parametrize('file', [
        HAYSTACK_PGT_FILE_01,
        BRICK_PGT_FILE_01
    ])
    def test_populate_from_file(self, file):
        # -- Setup
        templates = tt.load_template_file(file)
        assert len(templates) == 1

        template_data = templates[0]
        pgt = tt.PointGroupTemplate(**template_data)

        # -- Assert - template validates against schema
        assert pgt.is_valid

        # -- Setup
        pgt.populate_template_basics()

        # -- Assert - private variables are not empty
        assert bool(pgt._id)
        assert bool(pgt._symbol)
        assert bool(pgt._description)
        assert bool(pgt._schema_name)
        assert bool(pgt._schema_version)
        assert bool(pgt._telemetry_points)
        assert bool(pgt.template_schema)

        # -- Setup
        pgt.resolve_telemetry_point_types()

        # -- Assert
        assert len(pgt.telemetry_point_entity_templates) == 3

    @pytest.mark.parametrize('file', [
        HAYSTACK_PGT_FILE_01,
        BRICK_PGT_FILE_01
    ])
    def test_write(self, file):
        reset_base_template_instance_ids()
        # -- Setup
        template_data, pgt = populate_point_group_template_from_file(file)
        out_file = prep_for_write(OUTPUT_DIR, file, 'out', 'yaml')

        pgt.write(out_file)

        # -- Assert - file write created new file
        assert os.path.isfile(out_file)

        # -- Setup - reload new file
        output_template = tt.load_template_file(out_file)

        # A single PGT.write dumps as a single dict
        assert isinstance(output_template, dict)

        # -- Assert - the data should be the same as originally loaded
        assert output_template == template_data

    @pytest.mark.parametrize('file, symbol, schema, version', [
        (HAYSTACK_PGT_FILE_01, 'SD', tc.HAYSTACK, tc.V3_9_9),
        (BRICK_PGT_FILE_01, 'SD', tc.BRICK, tc.V1_1),
    ])
    def test_find_given_symbol_schema_version(self, file, symbol, schema, version):
        # -- Setup - reset all PGTs registered
        reset_base_template_instance_ids()
        reset_point_group_template_registration()
        _template, pgt = populate_point_group_template_from_file(file)

        # -- Assert - since instances was reset to empty set, and we are only creating a single
        # PGT, there should just be 1 for each of these.
        found = tt.PointGroupTemplate.find_given_symbol_schema_version(symbol, schema, version)
        assert len(found) == 1
        assert found[0] == pgt

    def test_find_given_symbol(self):
        # -- Setup - reset all PGTs registered
        symbol = 'SD'
        reset_base_template_instance_ids()
        reset_point_group_template_registration()
        _haystack_template, hpgt = populate_point_group_template_from_file(HAYSTACK_PGT_FILE_01)
        _brick_template, bpgt = populate_point_group_template_from_file(BRICK_PGT_FILE_01)

        found = tt.PointGroupTemplate.find_given_symbol(symbol)
        assert len(found) == 2
        assert hpgt in found
        assert bpgt in found


class TestEquipmentTemplate:

    def test_bad_template_type_throws_template_validation_error(self, equipment_template_bad_template_type):
        try:
            tt.EquipmentTemplate(**equipment_template_bad_template_type)

            # Should not reach here
            assert False is True
        except te.TemplateValidationError as e:
            assert str(e) == 'template_type must be: equipment-template'

    @pytest.mark.parametrize('file, expected_type', [
        (HAYSTACK_EQ_FILE_01, (tc.PHIOT_3_9_9, 'coolingOnly-vav')),
        (BRICK_EQ_FILE_01, (tc.BRICK_1_1, 'Variable_Air_Volume_Box')),
    ])
    def test_template_extension_resolves_to_expected_equip_class(self, file, expected_type):
        # -- Setup
        reset_base_template_instance_ids()
        templates = tt.load_template_file(file)
        assert len(templates) == 1

        template_data = templates[0]
        eq = tt.EquipmentTemplate(**template_data)

        # -- Assert - equipment template is valid
        assert eq.is_valid

        # -- Setup - populate basics
        eq.populate_template_basics()
        eq.resolve_extends()

        assert eq.extends == expected_type

    @pytest.mark.parametrize('pgt_file, eqt_file', [
        (HAYSTACK_PGT_FILE_01, HAYSTACK_EQ_FILE_01),
        (BRICK_PGT_FILE_01, BRICK_EQ_FILE_01)
    ])
    def test_resolve_telemetry_point_types(self, pgt_file, eqt_file):
        # -- Setup - reset PGTs to 0 and populate
        reset_base_template_instance_ids()
        reset_point_group_template_registration()

        # -- Setup
        eqt = populate_equipment_template_from_file(eqt_file)
        print(eqt._template)
        eqt.resolve_telemetry_point_types()

        # -- Assert - An entity template will have resolved
        assert len(eqt.telemetry_point_entity_templates) == 1
        # -- Assert - The PGT will not have resolved
        assert len(eqt.point_group_templates) == 0
        assert not eqt.fully_resolved

        # -- Setup - We now create a PGT and try to resolve again
        _haystack_template, hpgt = populate_point_group_template_from_file(pgt_file)
        eqt.resolve_telemetry_point_types()

        # -- Assert - they should have both resolved and
        assert len(eqt.point_group_templates) == 1
        assert len(eqt.telemetry_point_entity_templates) == 1
        assert eqt.fully_resolved
        for et in eqt.get_all_points_as_entity_templates():
            print(et.get_simple_classes())
