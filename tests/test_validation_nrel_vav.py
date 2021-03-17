import os

import pytest
from rdflib import Namespace, SH
from pyshacl import validate

from tasty import constants as tc
from tasty import graphs as tg
from tests.conftest import get_single_node_validation_query, assert_remove_markers, write_csv, \
    get_parent_node_validation_query, get_severity_query, run_another, get_validate_dir

SAMPLE = Namespace('urn:sample/')


class TestNRELVavCoolingOnly:
    @pytest.mark.parametrize('shape_name, target_node', [
        [tc.PH_SHAPES_CORE['NREL-VAV-SD-Cooling-Only-Shape'], SAMPLE['NREL-VAV-01']]
    ])
    def test_is_valid(self, get_haystack_nrel_data, get_haystack_nrel_generated_shapes, shape_name, target_node):
        # -- Setup
        data_graph = get_haystack_nrel_data
        shapes_graph = get_haystack_nrel_generated_shapes
        ont_graph = tg.load_ontology(tc.HAYSTACK, tc.V3_9_9)
        validate_dir = os.path.join(os.path.dirname(__file__), 'output/validate')
        if not os.path.isdir(validate_dir):
            os.mkdir(validate_dir)

        # -- Setup
        shapes_graph.add((shape_name, SH.targetNode, target_node))

        result = validate(data_graph, shacl_graph=shapes_graph, ont_graph=ont_graph)
        conforms, results_graph, results = result

        # -- Serialize results
        f = 'TestNRELVavCoolingOnly' + '_valid.ttl'
        output_file = os.path.join(validate_dir, f)
        results_graph.serialize(output_file, format='turtle')

        # -- Assert conforms
        assert conforms
