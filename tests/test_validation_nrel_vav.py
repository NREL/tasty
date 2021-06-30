import os

import pytest
from rdflib import Namespace, SH
from pyshacl import validate

from tasty import constants as tc
from tasty import graphs as tg
from tests.conftest import run_another, get_validate_dir


NAMESPACE = Namespace('urn:sample/')
SHAPE = 'NREL-VAV-SD-Cooling-Only-Shape'
SAMPLE = 'NREL-VAV-01'
TTL_FILE_PREFIX = 'TestNRELVavCoolingOnly'


class TestNRELVavCoolingOnly:

    @pytest.mark.parametrize('shape_name, target_node', [
        [tc.PH_SHAPES_NREL[SHAPE], NAMESPACE[SAMPLE]]
    ])
    def test_is_valid(self, get_haystack_nrel_data, get_haystack_all_generated_shapes, shape_name, target_node):
        # -- Setup
        data_graph = get_haystack_nrel_data
        shapes_graph = get_haystack_all_generated_shapes
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_10)
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Serialize results
        f = TTL_FILE_PREFIX + '_valid.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert conforms
        if not conforms:
            # serialize shapes graph for debugging
            shapes_graph.serialize(TTL_FILE_PREFIX + '-test_is_valid.ttl', format='turtle')
        assert conforms

    @pytest.mark.parametrize('shape_name, target_node, remove_from_node, remove_markers, num_runs', [
        [
            tc.PH_SHAPES_NREL[SHAPE], NAMESPACE[SAMPLE],
            NAMESPACE['NREL-VAV-01-ZoneRelativeHumidityShape'], ['zone'], 2
        ],
    ])
    def test_is_invalid(self, get_haystack_nrel_data, get_haystack_all_generated_shapes, shape_name, target_node,
                        remove_from_node,
                        remove_markers, num_runs):
        # Set version for constants
        tc.set_default_versions(haystack_version=tc.V3_9_10)

        # -- Setup
        data_graph = get_haystack_nrel_data
        shapes_graph = get_haystack_all_generated_shapes
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_10)
        validate_dir = get_validate_dir()

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))
        for marker in remove_markers:
            ns = tg.get_namespaces_given_term(ont_graph, marker)
            if tg.has_one_namespace(ns):
                ns = ns[0]
                data_graph.remove((remove_from_node, tc.PH_DEFAULT.hasTag, ns[marker]))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Serialize results
        f = 'TestNREL_' + '_'.join(remove_markers) + '_remove.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # Grab easy to read info
        str_name = str(shape_name)
        str_name = str_name.split('#')[1]
        target_name = str(target_node)
        target_name = target_name.split(str(NAMESPACE))[1]

        # serialize shapes graph for debugging
        f = f"{str_name}_{target_name}" + '_'.join(remove_markers) + '_remove-shapes-graph.ttl'
        shapes_graph.serialize(os.path.join(validate_dir, f), format='turtle')
        # -- Assert does not conform
        assert not conforms

        # Here we iterate through to add target nodes
        # based on
        for run in range(num_runs - 1):
            print(f"Iteration {run} on {str_name}")
            conforms, results_graph, results = run_another(results_graph, shapes_graph, data_graph, ont_graph)

        # -- Serialize results
        f = f"{str_name}_{target_name}" + '_'.join(remove_markers) + '_remove-results-graph.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert does not conform
        assert not conforms
