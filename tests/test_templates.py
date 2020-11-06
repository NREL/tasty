import os

from typing import List
import pytest
from unittest import TestCase
from rdflib.namespace import Namespace

from tasty import templates as tt
from tasty import constants as tc
import tasty.graphs as tg
import tasty.exceptions as te

FILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
SINGLE_TEMPLATE_FILE_PATH = os.path.join(FILES_DIR, 'point-group-template-1.yaml')
SCHEMA_FILE_PATH = os.path.join(tc.SCHEMAS_DIR, 'template.schema.json')


class TestTemplateFunctions:
    def test_point_group_template_is_single_dict(self):
        # -- Setup
        template_path = SINGLE_TEMPLATE_FILE_PATH
        assert os.path.isfile(template_path)

        template = tt.load_template_file(template_path)

        # -- Assert
        assert len(template) == 1
        assert isinstance(template[0], dict)

    def test_exemplary_file_is_valid(self):
        # -- Setup
        template = tt.load_template_file(SINGLE_TEMPLATE_FILE_PATH)
        schema = tt.load_template_schema(SCHEMA_FILE_PATH)
        template = template[0]

        # -- Assert
        is_valid, _ = tt.validate_template_against_schema(template, schema)
        assert is_valid

    @pytest.mark.parametrize("key,error_message", [
        ("id", "'id' is a required property"),
        ("symbol", "'symbol' is a required property"),
        ("description", "'description' is a required property"),
    ])
    def test_file_is_not_valid_if_keys_missing(self, key, error_message):
        # -- Setup
        template = tt.load_template_file(SINGLE_TEMPLATE_FILE_PATH)
        schema = tt.load_template_schema(SCHEMA_FILE_PATH)
        template = template[0]

        # -- Act
        del template[key]

        # -- Assert
        is_valid, err = tt.validate_template_against_schema(template, schema)
        assert not is_valid
        assert err == error_message

    @pytest.mark.parametrize("key,value,error", [
        ("schema", "BAD", "'BAD' is not one of ['Brick', 'Haystack']"),
        ("version", "1234", "'1234' is not one of ['1.1', '3.9.9']"),
    ])
    def test_file_is_not_valid_if_keys_have_wrong_values(self, key, value, error):
        # -- Setup
        template = tt.load_template_file(SINGLE_TEMPLATE_FILE_PATH)
        schema = tt.load_template_schema(SCHEMA_FILE_PATH)
        template = template[0]

        # -- Act
        template[key] = value

        # -- Assert
        is_valid, err = tt.validate_template_against_schema(template, schema)
        assert not is_valid
        assert err == error


class TestReturnNamespacedTerms(TestCase):
    def test_resolves_typical_haystack_tagset(self):
        # -- Setup
        ont = tg.load_ontology('Haystack', '3.9.9')
        entity_type = 'discharge-air-flow-sensor-point'

        # -- Act
        tags = tt._get_namespaced_terms(ont, entity_type)

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
        tags = tt._get_namespaced_terms(ont, entity_type)

        # -- Assert
        assert len(tags) == 5

    def test_resolves_brick_class(self):
        # -- Setup
        ont = tg.load_ontology('Brick', '1.1')
        entity_type = 'Discharge_Air_Flow_Sensor'

        # -- Act
        tags = tt._get_namespaced_terms(ont, entity_type)
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
            tt._get_namespaced_terms(ont, entity_type)

        # -- Assert
        assert str(context.exception) == "Candidate 'this' not found in any namespaces in the provided ontology"

    def test_errors_when_term_found_in_multiple_namespaces(self):
        # -- Setup
        ont = tg.load_ontology('Brick', '1.1')
        entity_type = 'Discharge-Temperature'

        # -- Act
        with self.assertRaises(te.MultipleTermsFoundError) as context:
            tt._get_namespaced_terms(ont, entity_type)
        ex = "Candidate 'Temperature' found in multiple namespaces: [rdflib.term.URIRef(" \
             "'https://brickschema.org/schema/1.1/Brick#'), rdflib.term.URIRef(" \
             "'https://brickschema.org/schema/1.1/BrickTag#')]"

        # -- Assert
        assert str(context.exception) == ex


class TestHaystackGetEntities:
    def test_passes_when_single_valid_entity(self):
        # -- Setup
        ont = tg.load_ontology('Haystack', '3.9.9')
        entity_type = 'discharge-air-flow-sensor-point'
        valid_namespaced_terms = tt._get_namespaced_terms(ont, entity_type)

        # -- Act
        entity_types, typing_properties = tt._haystack_get_entities_and_typing_properties(ont, valid_namespaced_terms)
        entity_types_list = list(entity_types)
        typing_properties_list = list(typing_properties)

        # -- Assert
        assert len(entity_types) == 1
        assert len(typing_properties) == 4
        assert isinstance(entity_types, set)
        assert tc.PHIOT_3_9_9, 'point' == entity_types_list[0]
        assert (tc.PHSCIENCE_3_9_9, 'air') in typing_properties_list

    def test_passes_when_multiple_valid_entities(self):
        # -- Setup
        ont = tg.load_ontology('Haystack', '3.9.9')
        entity_type = 'fan-motor-sensor-point'
        tags = tt._get_namespaced_terms(ont, entity_type)
        entity_types, typing_properties = tt._haystack_get_entities_and_typing_properties(ont, tags)

        # -- Act
        assert len(entity_types) == 2


class TestEntityTemplate:
    def test_create_new_haystack_entity_template(self):
        # -- Setup
        ont = tg.load_ontology('Haystack', '3.9.9')
        properties = {
            'curVal': None,
            'kind': 'Number',
            'unit': 'cfm'
        }
        all_metadata = {
            'discharge': None,
            'air': None,
            'temp': None,
            'sensor': None,
            'point': None,
            'curVal': None,
            'kind': 'Number',
            'unit': 'cfm'
        }

        # -- Act
        valid_namespaced_terms = tt._get_namespaced_terms(ont, 'discharge-air-temp-sensor-point')
        entities, typing_properties = tt._haystack_get_entities_and_typing_properties(ont, valid_namespaced_terms)
        other_properties = tt._haystack_get_other_properties(ont, properties)

        # -- Assert
        assert isinstance(entities, set)
        assert isinstance(other_properties, dict)
        et = tt.EntityTemplate(entities, typing_properties, other_properties)
        assert et.get_entity_type() == set(['point'])
        assert et.get_typing_info() == set(['discharge', 'air', 'temp', 'sensor', 'point'])
        assert et.get_other_properties() == properties
        assert et.get_all_metadata_simple() == all_metadata


class TestResolveTelemetryPointsToEntityTemplates:
    def test_valid_telemetry_points(self):
        # -- Setup
        template = tt.load_template_file(SINGLE_TEMPLATE_FILE_PATH)
        template = template[0]
        tel = "telemetry_point_types"
        assert tel in template.keys()

        # -- Act
        points = template[tel]
        schema = template['schema']
        version = template['version']
        entity_templates = tt.resolve_telemetry_points_to_entity_templates(points, schema, version)
        print(entity_templates)
        assert isinstance(entity_templates, List)
        assert len(entity_templates) == 3
        for et in entity_templates:
            assert isinstance(et, tt.EntityTemplate)
