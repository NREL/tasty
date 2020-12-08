import os

import pytest
from unittest import TestCase
from rdflib.namespace import Namespace
from frozendict import frozendict
import pickle

import tasty.templates as tt
import tasty.constants as tc
import tasty.graphs as tg
import tasty.exceptions as te
from tests.conftest import populate_pgt_from_file, prep_for_write, reset_pgt_all_templates_to_empty_set

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
            print(type(v))
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
        ("description", "'description' is a required property"),
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
        ont = tg.load_ontology('Haystack', '3.9.9')
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
        ont = tg.load_ontology('Haystack', '3.9.9')
        entity_type = 'discharge-air-discharge-flow-sensor-point'

        # -- Act
        tags = tt.get_namespaced_terms(ont, entity_type)

        # -- Assert
        assert len(tags) == 5

    def test_resolves_brick_class(self):
        # -- Setup
        ont = tg.load_ontology('Brick', '1.1')
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
        ont = tg.load_ontology('Haystack', '3.9.9')
        entity_type = 'this-sensor'

        # -- Act
        with self.assertRaises(te.TermNotFoundError) as context:
            tt.get_namespaced_terms(ont, entity_type)

        # -- Assert
        assert str(context.exception) == "Candidate 'this' not found in any namespaces in the provided ontology"

    def test_errors_when_term_found_in_multiple_namespaces(self):
        # -- Setup
        ont = tg.load_ontology('Brick', '1.1')
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
    @pytest.mark.parametrize("tagset, classes, markers, fields", [
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
    def test_resolves_as_expected(self, tagset, classes, markers, fields):
        ont = tg.load_ontology('Haystack', '3.9.9')
        valid_namespaced_terms = tt.get_namespaced_terms(ont, tagset)
        structured = tt.hget_entity_classes(ont, set(valid_namespaced_terms))
        assert list(structured.keys()) == ['classes', 'markers', 'fields']
        assert structured['classes'] == classes
        assert structured['markers'] == markers
        assert structured['fields'] == fields


class TestEntityTemplate:

    # This is done at the onset, as classes remain in memory space per TestClass
    #
    def test_register_template(self):
        assert len(tt.EntityTemplate.all_templates) == 0

    def test_blank_template_methods_dont_fail(self):
        et = tt.EntityTemplate(entity_classes=set(), typing_properties=set(), fields=set())
        assert et.get_simple_classes() == set()
        assert et.get_simple_typing_info() == set()
        assert et.get_simple_fields() == {}
        assert et.get_namespaces() == set()
        assert et in tt.EntityTemplate.all_templates  # checks the template was registered

    def test_create_new_haystack_entity_template(self):
        # -- Setup
        ont = tg.load_ontology('Haystack', '3.9.9')
        point_type_string = 'cur-his-discharge-air-temp-sensor-point'
        fields = {
            'curVal': {
                '_kind': 'number',
                'val': None
            },
            'unit': 'cfm'
        }
        # -- Setup - define expectations
        simple_classes = {'his-point', 'cur-point'}
        simple_typing_info = {'discharge', 'air', 'temp', 'sensor', 'his-point', 'cur-point'}
        simple_fields = {'curVal': {'_kind': 'number', 'val': None}, 'unit': {'val': 'cfm'}}
        all_ns = {
            tc.PH_3_9_9,
            tc.PHIOT_3_9_9,
            tc.PHSCIENCE_3_9_9
        }

        # -- Act
        ns_terms = tt.get_namespaced_terms(ont, point_type_string)
        ns_fields = tt.get_namespaced_terms(ont, fields)
        structured_terms = tt.hget_entity_classes(ont, ns_terms)

        # -- Assert
        et = tt.EntityTemplate(structured_terms['classes'], structured_terms['markers'], ns_fields)
        assert et.get_simple_classes() == simple_classes
        assert et.get_simple_typing_info() == simple_typing_info
        assert et.get_simple_fields() == simple_fields
        assert et.get_namespaces() == all_ns
        assert et in tt.EntityTemplate.all_templates  # checks the template was registered

    def test_create_new_brick_entity_template(self):
        # -- Setup
        ont = tg.load_ontology('Brick', '1.1')
        point_type_string = 'Discharge_Air_Flow_Sensor'
        ns_terms = tt.get_namespaced_terms(ont, point_type_string)

        # -- Setup - define expectations
        simple_classes = {point_type_string}
        simple_typing_info = {point_type_string}
        simple_fields = {}
        all_ns = {
            tc.BRICK_1_1
        }

        et = tt.EntityTemplate(ns_terms, set(), set())
        assert et.get_simple_classes() == simple_classes  # Only a single class
        assert et.get_simple_typing_info() == simple_typing_info  # Additional typing info not relevant for Brick at this time
        assert et.get_simple_fields() == simple_fields  # No DataTypeProperties available in Brick as of 1.1
        assert et.get_namespaces() == all_ns
        assert et in tt.EntityTemplate.all_templates  # checks the template was registered

    @pytest.mark.parametrize('class_to_find, expected_number_templates', [
        ((tc.PHIOT_3_9_9, 'cur-point'), 1),
        ((tc.PHIOT_3_9_9, 'equip'), 0)
    ])
    def test_find_with_class(self, class_to_find, expected_number_templates):
        # -- Setup
        tg.load_ontology('Haystack', '3.9.9')
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


class TestPointGroupTemplate:
    @pytest.mark.parametrize('file', [
        HAYSTACK_PGT_FILE_01,
        BRICK_PGT_FILE_01
    ])
    def test_populate_from_file(self, file):
        # -- Setup
        templates = tt.load_template_file(file)
        assert len(templates) == 1

        template_data = templates[0]
        pgt = tt.PointGroupTemplate(template_data)

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
        assert len(pgt.telemetry_point_entities) == 3

    @pytest.mark.parametrize('file', [
        HAYSTACK_PGT_FILE_01,
        BRICK_PGT_FILE_01
    ])
    def test_write(self, file):
        # -- Setup
        template_data, pgt = populate_pgt_from_file(file)
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

    @pytest.mark.parametrize('file', [
        HAYSTACK_PGT_FILE_01,
        BRICK_PGT_FILE_01
    ])
    def test_pickle(self, file):
        template_data, pgt = populate_pgt_from_file(file)
        out_file = prep_for_write(OUTPUT_DIR, file, 'pickle', 'pkl')

        pgt.pickle(out_file)

        # -- Assert - pickled object exists
        assert os.path.isfile(out_file)

        with open(out_file, 'rb') as f:
            pgt_out = pickle.load(f)

        assert isinstance(pgt_out, tt.PointGroupTemplate)

        # These are now different objects, so will not be equivalent
        assert pgt_out != pgt

        # Need a way to check that these two are equivalen / similar,
        # even though they're not the same object, they still represent
        # the same information

    @pytest.mark.parametrize('file, symbol, schema, version', [
        (HAYSTACK_PGT_FILE_01, 'SD', 'Haystack', '3.9.9'),
        (BRICK_PGT_FILE_01, 'SD', 'Brick', '1.1'),
    ])
    def test_find_given_symbol_schema_version(self, file, symbol, schema, version):
        # -- Setup - reset all PGTs registered
        reset_pgt_all_templates_to_empty_set()
        _template, pgt = populate_pgt_from_file(file)

        # -- Assert - since all_templates was reset to empty set, and we are only creating a single
        # PGT, there should just be 1 for each of these.
        found = tt.PointGroupTemplate.find_given_symbol_schema_version(symbol, version, schema)
        assert len(found) == 1
        assert found[0] == pgt

    def test_find_given_symbol(self):
        # -- Setup - reset all PGTs registered
        symbol = 'SD'
        reset_pgt_all_templates_to_empty_set()
        _haystack_template, hpgt = populate_pgt_from_file(HAYSTACK_PGT_FILE_01)
        _brick_template, bpgt = populate_pgt_from_file(BRICK_PGT_FILE_01)

        found = tt.PointGroupTemplate.find_given_symbol(symbol)
        assert len(found) == 2
        assert hpgt in found
        assert bpgt in found


class TestEquipmentTemplate:
    @pytest.mark.parametrize('file, expected_type', [
        (HAYSTACK_EQ_FILE_01, (tc.PHIOT_3_9_9, 'coolingOnly-vav')),
        (BRICK_EQ_FILE_01, (tc.BRICK_1_1, 'Variable_Air_Volume_Box')),
    ])
    def test_populate_from_file_extension_resolves(self, file, expected_type):
        # -- Setup
        templates = tt.load_template_file(file)
        assert len(templates) == 1

        template_data = templates[0]
        eq = tt.EquipmentTemplate(template_data)

        # -- Assert - equipment template is valid
        assert eq.is_valid

        # -- Setup - populate basics
        eq.populate_template_basics()
        eq.resolve_extends()

        assert eq.extends == expected_type

    # @pytest.mark.parametrize('file', [
    #     HAYSTACK_EQ_FILE_01,
    # ])
    # def test_resolve_telemetry_point_types(self, file):
