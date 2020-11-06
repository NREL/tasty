from unittest import TestCase
import pytest

from rdflib import Graph

from tasty import graphs as tg
from tasty import constants as tc


class TestGetVersionedGraph:
    def test_get_versioned_graph(self):
        # -- Setup
        schema = 'Brick'
        version = '1.1'

        # -- Act
        g = tg.get_versioned_graph(schema, version)

        # -- Assert
        assert isinstance(g, Graph)

    @pytest.mark.parametrize("schema,version,namespaces", [
        ("Brick", "1.1", [
            ('brick', tc.BRICK_1_1),
            ('tag', tc.TAG_1_1),
            ('bsh', tc.BSH_1_1)
        ]),
        ("Haystack", "3.9.9", [
            ('ph', tc.PH_3_9_9),
            ('phIoT', tc.PHIOT_3_9_9),
            ('phIct', tc.PHICT_3_9_9),
            ('phScience', tc.PHSCIENCE_3_9_9)
        ])
    ])
    def test_get_versioned_graph_has_correct_namespaces(self, schema, version, namespaces):
        # -- Setup
        # -- Act
        g = tg.get_versioned_graph(schema, version)

        # Cast generator to list
        graph_namespaces = list(g.namespaces())

        # -- Assert
        for ns in namespaces:
            assert ns in graph_namespaces

    @pytest.mark.parametrize("schema,version,namespaces", [
        ("Brick", "1.1", [
            ('ph', tc.PH_3_9_9),
        ]),
        ("Haystack", "3.9.9", [
            ('brick', tc.BRICK_1_1),
        ])
    ])
    def test_get_versioned_graph_doesnt_have_incorrect_namespaces(self, schema, version, namespaces):
        # -- Setup
        # -- Act
        g = tg.get_versioned_graph(schema, version)

        # Cast generator to list
        graph_namespaces = list(g.namespaces())

        # -- Assert
        for ns in namespaces:
            assert ns not in graph_namespaces


class TestIsValidSchemaAndVersion(TestCase):
    def test_is_invalid_when_unsupported_schema_specified(self):
        # -- Setup
        schema = 'ABC123'
        version = '1.1'
        err = f"Schema: {schema} not supported.  Supported schemas include: {list(tc.SUPPORTED_SCHEMAS.keys())}"

        # -- Act
        with self.assertRaises(Exception) as context:
            tg.is_valid_schema_and_version(schema, version)

        # -- Assert
        self.assertEqual(str(context.exception), err)

    def test_is_invalid_when_unsupported_schema_version_specified(self):
        # -- Setup
        schema = 'Haystack'
        version = '1.1'
        err = f"Schema: {schema} with version: {version} not supported.  Supported versions include: {list(tc.SUPPORTED_SCHEMAS[schema])}"

        # -- Act
        with self.assertRaises(Exception) as context:
            tg.is_valid_schema_and_version(schema, version)

        # -- Assert
        self.assertEqual(str(context.exception), err)


class TestLoadOntology:
    @pytest.mark.parametrize("schema,version", [
        ("Brick", "1.1"),
        ("Haystack", "3.9.9")
    ])
    def test_load_ontology(self, schema, version):
        # -- Setup
        g = tg.load_ontology(schema, version)

        assert isinstance(g, Graph)
